"""Inspect Codex review and optionally send one bounded, SHA-scoped retry.

GitHub comments retain request history across coordinator restarts. The mutable
bot summary is a scheduling hint only; it never establishes review completion.
"""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import subprocess

from milestone import github
from integration import fresh_bot_receipt, fresh_bot_reaction, timestamp


REPOSITORY = 'clemarc/fava'
BOT = 'chatgpt-codex-connector[bot]'
BOT_ID = 199175422
RETRY_AFTER_SECONDS = 20 * 60
HARD_DEADLINE_SECONDS = 45 * 60
POLL_SECONDS = 60
MARKER = 'fava-codex-request:v1'


def bot_actor(value):
    user = value.get('user', {})
    return user.get('login') == BOT and user.get('id') == BOT_ID and user.get('type') == 'Bot'


def request_body(head, attempt):
    metadata = json.dumps({'attempt': attempt}, separators=(',', ':'))
    return f'@codex review {head}\n\n<!-- {MARKER} {metadata} -->'


def requests_for(comments, head, number, head_time, now):
    requests, ambiguous = [], []
    for comment in comments:
        body = comment.get('body', '')
        if (comment.get('user', {}).get('login') != 'clemarc'
                or not re.search(r'(?m)^@codex review(?:\s|$)', body)
                or head not in re.findall(r'\b[0-9a-f]{40}\b', body)):
            continue
        try:
            valid = (comment.get('issue_url') == f'https://api.github.com/repos/{REPOSITORY}/issues/{number}'
                     and comment.get('created_at') == comment.get('updated_at')
                     and re.findall(r'\b[0-9a-f]{40}\b', body) == [head]
                     and head_time < timestamp(comment['created_at']) <= now
                     and type(comment.get('id')) is int)
        except (KeyError, ValueError, TypeError):
            valid = False
        if valid:
            requests.append(comment)
        else:
            ambiguous.append(comment.get('id'))
    return sorted(requests, key=lambda c: (timestamp(c['created_at']), c['id'])), ambiguous


def completion(root, head, number, head_time, now, requests, comments, reviews, reactions):
    """Use authenticated, immutable/current-head proof, never summary status."""
    for review in reviews:
        try:
            if (bot_actor(review) and review.get('commit_id') == head
                    and review.get('state') in {'APPROVED', 'COMMENTED', 'CHANGES_REQUESTED'}
                    and head_time < timestamp(review['submitted_at']) < now):
                return {'kind': 'review', 'id': review['id'], 'url': review.get('html_url')}
        except (KeyError, ValueError, TypeError):
            continue
    for request in requests:
        for comment in comments:
            if bot_actor(comment) and fresh_bot_receipt(root, request, comment, head, number, head_time, now):
                return {'kind': 'receipt', 'id': comment['id'], 'request': request['id'],
                        'url': comment.get('html_url')}
        actual = [r for r in reactions.get(request['id'], []) if bot_actor(r)
                  and head_time < timestamp(r['created_at']) < now]
        if fresh_bot_reaction(request, actual, head, number):
            return {'kind': 'reaction', 'request': request['id'], 'url': request.get('html_url')}
    return None


def summary_state(comments, head):
    summaries = []
    for comment in comments:
        if not bot_actor(comment):
            continue
        match = re.search(r'<!-- codex-review-state:v1 (.*?) -->', comment.get('body', ''), re.S)
        if not match:
            continue
        try:
            state = json.loads(match[1])['code_review']
            if state.get('commit_sha') == head:
                summaries.append((timestamp(comment['updated_at']), state.get('status')))
        except (KeyError, ValueError, TypeError):
            continue
    if not summaries:
        return None, None
    latest = max(at for at, _ in summaries)
    states = {state for at, state in summaries if at == latest}
    return (next(iter(states)) if len(states) == 1 else 'ambiguous'), latest


def plan(root, head, number, head_time, comments, reviews, reactions, now,
         retry_after=RETRY_AFTER_SECONDS, hard_deadline=HARD_DEADLINE_SECONDS):
    if not re.fullmatch(r'[0-9a-f]{40}', head):
        raise ValueError('actual full head SHA required')
    if not 0 < retry_after < hard_deadline:
        raise ValueError('retry interval must be positive and below the hard deadline')
    requests, ambiguous = requests_for(comments, head, number, head_time, now)
    proof = completion(root, head, number, head_time, now, requests, comments, reviews, reactions)
    state, summary_time = summary_state(comments, head)
    active_states = {'running', 'in_progress', 'queued', 'pending'}
    failed_states = {'failed', 'error', 'cancelled', 'canceled'}
    # A terminal summary from the prior attempt is not the new request's result.
    # Equal-second ordering is ambiguous too, so only a strictly later terminal
    # update can describe the latest request. Active hints still prevent writes.
    stale_terminal = bool(requests and state in failed_states | {'completed'}
                          and summary_time <= timestamp(requests[-1]['created_at']))
    effective_state = None if stale_terminal else state
    # Mutable summaries cannot reset a timer. Before any manual request, an
    # automatic running review is conservatively bounded by the head commit.
    origin = timestamp(requests[0]['created_at']) if requests else head_time if state in active_states else None
    age = (now - origin).total_seconds() if origin else 0
    result = dict(head=head, pr=number, request_comments=[r['id'] for r in requests],
                  retry_count=max(0, len(requests) - 1), poll_seconds=POLL_SECONDS,
                  retry_after_seconds=retry_after, hard_deadline_seconds=hard_deadline,
                  summary_status=state, age_seconds=max(0, int(age)),
                  summary_stale=stale_terminal,
                  age_basis='first_request' if requests else 'head_commit' if origin else None,
                  completion=proof)
    if proof:
        return dict(result, decision='complete', reason='actual current-head completion; findings still require disposition')
    if ambiguous:
        return dict(result, decision='blocked', reason='edited or ambiguous current-head request history',
                    ambiguous_comments=ambiguous)
    if origin and age >= hard_deadline:
        return dict(result, decision='blocked', reason='hard review deadline reached; owner disposition required')
    if effective_state in active_states:
        return dict(result, decision='wait', reason='bot reports active current-head review; do not duplicate it')
    if effective_state is not None and effective_state not in failed_states | {'completed'}:
        return dict(result, decision='blocked', reason='unsupported or ambiguous current-head summary status')
    if not requests:
        return dict(result, decision='request', attempt=0,
                    reason='no valid current-head request or completion; establish fresh request evidence')
    if effective_state == 'completed':
        return dict(result, decision='blocked', reason='summary cannot establish completion; inspect actual review evidence')
    if len(requests) >= 2:
        if effective_state in failed_states:
            return dict(result, decision='blocked', reason='single automatic retry failed; owner disposition required')
        return dict(result, decision='wait', reason='single automatic retry already used; wait until hard deadline')
    if effective_state in failed_states or age >= retry_after:
        return dict(result, decision='retry', attempt=1, reason='failed or unacknowledged request; one retry permitted')
    return dict(result, decision='wait', reason='request remains within observed review allowance')


def pages(endpoint, api):
    return [item for page in api('api', '--paginate', '--slurp', endpoint) for item in page]


def inspect_review(root, number, now=None, api=github, retry_after=RETRY_AFTER_SECONDS,
                   hard_deadline=HARD_DEADLINE_SECONDS):
    now = now or datetime.now(timezone.utc)
    pr = api('api', f'repos/{REPOSITORY}/pulls/{number}')
    if pr.get('state') != 'open' or pr.get('draft') is not False:
        raise ValueError('review requests require an open, ready PR')
    head = pr['head']['sha']
    commit = api('api', f'repos/{REPOSITORY}/commits/{head}')
    head_time = timestamp(commit['commit']['committer']['date'])
    # Prefix disambiguation in the existing receipt verifier uses actual Git
    # objects. Fetch is a repository read, never a branch update or publication.
    subprocess.run(['git', '-C', str(root), 'fetch', 'origin', head], check=True, capture_output=True)
    comments = pages(f'repos/{REPOSITORY}/issues/{number}/comments?per_page=100', api)
    reviews = pages(f'repos/{REPOSITORY}/pulls/{number}/reviews?per_page=100', api)
    requests, _ = requests_for(comments, head, number, head_time, now)
    reactions = {r['id']: pages(f'repos/{REPOSITORY}/issues/comments/{r["id"]}/reactions?per_page=100', api)
                 for r in requests}
    return plan(root, head, number, head_time, comments, reviews, reactions, now, retry_after, hard_deadline)


def run(root, number, retry=False, api=github, now=None, **timing):
    result = inspect_review(root, number, now, api, **timing)
    if not retry or result['decision'] not in {'request', 'retry'}:
        return result
    # Re-read every live fact immediately before mutation. A response timeout is
    # ambiguous: stop and reconcile comments on the next invocation, never resend
    # automatically in the same call. One coordinator serializes these requests.
    result = inspect_review(root, number, now, api, **timing)
    if result['decision'] not in {'request', 'retry'}:
        return result
    body = request_body(result['head'], result['attempt'])
    try:
        comment = api('api', '--method', 'POST', f'repos/{REPOSITORY}/issues/{number}/comments', '-f', 'body=' + body)
    except (ValueError, subprocess.CalledProcessError):
        return dict(result, decision='reconcile', reason='ambiguous request outcome; inspect actual comments before retrying')
    return dict(result, decision='requested', posted_comment=comment['id'],
                reason='fresh request posted; poll without repeating the write')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pr', required=True, type=int)
    parser.add_argument('--retry', action='store_true', help='authorize initial request or single eligible retry')
    args = parser.parse_args()
    try:
        result = run(Path.cwd(), args.pr, args.retry)
        print(json.dumps(result, indent=2))
        raise SystemExit(1 if result['decision'] in {'blocked', 'reconcile'} else 0)
    except (ValueError, KeyError, TypeError, subprocess.CalledProcessError) as error:
        parser.exit(1, 'STOP: ' + str(error) + '\n')


if __name__ == '__main__':
    main()
