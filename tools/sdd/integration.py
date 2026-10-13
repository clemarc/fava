"""Read-only integration gate assessment; never merges or enables auto-merge."""
import argparse
import json
from pathlib import Path
import re
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / '.github/checks'))
import sdd
from milestone import github, inspect, read, ancestor
from lifecycle import planning_ref


def check_results(checks):
    results = {c['name']: c.get('conclusion') for c in checks if c.get('name')}
    # The repository's reusable workflow emits one named check per device family.
    # Do not mistake an absent aggregate name for missing native execution, or
    # accept just one successful matrix leg as both-family validation.
    families = ['ios-build-test / ios-build-test (iPhone)', 'ios-build-test / ios-build-test (iPad)']
    if any(name in results for name in families):
        results['ios-build-test'] = 'SUCCESS' if all(results.get(name) == 'SUCCESS' for name in families) else 'INCOMPLETE'
    return results


def evaluate(evidence):
    errors = []
    head, target = evidence.get('head'), evidence.get('target')
    if not head or not target or evidence.get('validated_head') != head or evidence.get('validated_target') != target:
        errors.append('validation is missing or stale for current head/target')
    for field in ['scope', 'dependencies', 'trailers', 'signatures', 'protected_target', 'structural_drift',
                  'semantic_drift', 'independent_review', 'findings_disposed']:
        if evidence.get(field) is not True:
            errors.append(field + ': verified evidence required')
    if evidence.get('base') != evidence.get('milestone_branch') or not str(evidence.get('base', '')).startswith('milestone/'):
        errors.append('task PR must target the registered milestone branch')
    if evidence.get('state') != 'OPEN' or evidence.get('draft') is not False:
        errors.append('task PR must be open and ready for review')
    if evidence.get('blocked_findings'):
        errors.append('unresolved critical correctness/security/scope/consistency findings')
    checks = evidence.get('checks', {})
    for name in ['sdd-quality', 'tooling-validation', 'ci-applicability', 'ci-required']:
        if checks.get(name) != 'SUCCESS':
            errors.append(name + ': current passing deterministic check required')
    if evidence.get('native_required'):
        if checks.get('ios-build-test') != 'SUCCESS' or not evidence.get('simulator_tests', 0) > 0 or not evidence.get('macos_build'):
            errors.append('actual macOS compilation and nonzero simulator tests required')
    if evidence.get('codex_configured') and evidence.get('codex_available'):
        if evidence.get('codex_review_head') != head or evidence.get('codex_review_complete') is not True:
            errors.append('Codex bot review pending/stale')
    elif evidence.get('codex_configured') and not evidence.get('codex_unavailability_evidence'):
        errors.append('record actual Codex unavailability; do not infer it from silence')
    if evidence.get('correction_cycles', 0) > 2 and not evidence.get('owner_extra_cycles'):
        errors.append('two automatic correction cycles exhausted')
    return errors


def assess(root, identifier, number, evidence_comment=None):
    context = inspect(root, identifier, 'implement')
    pr = github('pr', 'view', str(number), '--repo', 'clemarc/fava', '--json',
                'number,state,isDraft,headRefName,headRefOid,baseRefName,baseRefOid,commits,statusCheckRollup,reviews,url')
    checkpoint = pr['headRefName'].startswith(context['checkpoint_branch_prefix'])
    if pr['baseRefName'] != context['milestone_branch'] or not pr['headRefName'].startswith((context['task_branch_prefix'], context['checkpoint_branch_prefix'])):
        raise ValueError('PR head/base does not match resolved task/integration branch')
    subprocess.run(['git', '-C', str(root), 'fetch', 'origin', pr['headRefOid']], check=True, capture_output=True)
    head, target = pr['headRefOid'], context['target_sha']
    from urllib.parse import quote
    rules = github('api', 'repos/clemarc/fava/rules/branches/' + quote(context['milestone_branch'], safe=''))
    types = {r['type'] for r in rules}
    protected = {'pull_request', 'required_signatures', 'required_status_checks', 'deletion', 'non_fast_forward'} <= types
    protected = protected and any(r['type'] == 'required_status_checks'
                                  and r.get('parameters', {}).get('strict_required_status_checks_policy')
                                  and any(c['context'] == 'ci-required' for c in r.get('parameters', {}).get('required_status_checks', [])) for r in rules)
    protected = protected and any(r['type'] == 'pull_request' and r.get('parameters', {}).get('required_review_thread_resolution') for r in rules)
    feature = context['feature']
    ledger = json.loads(read(root, head, context['ledger']))
    # Durable report is necessary, never sufficient: compare live evidence below.
    # Validation occurs after publication. A commit cannot contain its own SHA;
    # put the SHA-bound report in a coordinator PR comment, not a self-referential
    # ledger commit. The ledger preserves its URL after integration/checkpoint.
    if not evidence_comment and not checkpoint:
        evidence_comment = ledger['tasks'][pr['headRefName'].split('/')[-1].upper()].get('integration_comment')
    if not evidence_comment:
        raise ValueError('current-head coordinator evidence comment is required')
    report = github('api', f'repos/clemarc/fava/issues/comments/{evidence_comment}')
    if report['issue_url'] != f'https://api.github.com/repos/clemarc/fava/issues/{number}' or report['user']['login'] != 'clemarc':
        raise ValueError('integration report must be an owner-identity coordinator comment on this PR')
    evidence = json.loads(report['body'])
    evidence.update(head=head, target=target, base=pr['baseRefName'],
                    milestone_branch=context['milestone_branch'], state=pr['state'], draft=pr['isDraft'], protected_target=protected)
    if pr['baseRefOid'] != target:
        raise ValueError('GitHub target moved during assessment')
    commits = sdd.git(root, 'rev-list', f'{target}..{head}').splitlines()
    evidence['signatures'] = bool(commits) and all(github('api', f'repos/clemarc/fava/commits/{sha}')['commit']['verification']['verified'] for sha in commits)
    paths = sdd.git(root, 'diff', '--name-only', target, head).splitlines()
    ids = set()
    for sha in commits:
        ids.update(re.findall(sdd.TASK, ' '.join(sdd.trailers(sdd.git(root, 'show', '-s', '--format=%B', sha)).get('Task', []))))
    reviewed_revision = ledger.get('planning_revision') or context['preparation_approval']['sha']
    rows = {r[0]: r for r in sdd.task_rows(read(root, reviewed_revision, feature + '/tasks.md'))}
    allowed = set().union(*(sdd.task_paths(rows[t][2]) for t in ids if t in rows))
    shared = {feature + '/' + p for p in ['execution.json', 'tasks.md', 'decision-log.md']}
    evidence['scope'] = bool(ids) and ids <= set(rows) and set(paths) <= allowed | shared
    if checkpoint:
        evidence['scope'] = bool(paths) and set(paths) <= {feature + '/' + p for p in ['execution.json', 'tasks.md', 'decision-log.md']}
    evidence['dependencies'] = all(ledger['tasks'].get(dep, {}).get('state') == 'integrated'
                                   and ancestor(root, ledger['tasks'][dep]['merge_sha'], target)
                                   for t in ids if t in rows for dep in re.findall(sdd.TASK, rows[t][2]))
    errors = []
    for sha in commits:
        changed = sdd.git(root, 'diff-tree', '--no-commit-id', '-r', '--name-only', sha + '^1', sha).splitlines()
        errors += sdd.validate_commit(sdd.git(root, 'show', '-s', '--format=%B', sha), changed, lambda p: read(root, sha, p))
        if sdd.implementation_paths(changed):
            planning_ref(root, context['main_sha'], sha, feature, sdd.git)
    evidence['trailers'] = not errors
    evidence['checks'] = check_results(pr['statusCheckRollup'])
    from native import classify
    evidence['native_required'] = classify(paths, sdd.git(root, 'ls-tree', '-r', '--name-only', head).splitlines(),
                                          sdd.git(root, 'ls-tree', '-r', '--name-only', target).splitlines()) == 'required'
    # Reviews may be COMMENTED by a separate Cloud subagent, with its report URL;
    # an implementation worker's own ledger assertion cannot supply that report.
    review = evidence.get('independent_review_url')
    threads = github('api', '--paginate', '--slurp', f'repos/clemarc/fava/pulls/{number}/comments?per_page=100')
    comments = [c for page in threads for c in page]
    reviews = github('api', '--paginate', '--slurp', f'repos/clemarc/fava/pulls/{number}/reviews?per_page=100')
    reviews = [r for page in reviews for r in page]
    evidence['codex_configured'] = True  # Current repository configuration; do not silently bypass.
    bot = [r for r in reviews if r['user']['login'] == 'chatgpt-codex-connector[bot]' and r['commit_id'] == head]
    evidence['codex_review_head'] = head if bot else None
    evidence['codex_review_complete'] = bool(bot)
    # Bot thumbs-up reports may be on the explicit SHA-scoped review request;
    # coordinator records that URL and checks the reaction's actor and timestamp.
    request_id = evidence.get('codex_request_comment')
    if request_id and not bot:
        request = github('api', f'repos/clemarc/fava/issues/comments/{request_id}')
        reactions = github('api', f'repos/clemarc/fava/issues/comments/{request_id}/reactions')
        if head in request['body'] and any(r['content'] == '+1' and r['user']['login'] == 'chatgpt-codex-connector[bot]' for r in reactions):
            evidence['codex_review_head'], evidence['codex_review_complete'] = head, True
    evidence['review_comments'] = [{'url': c['html_url'], 'body': c['body']} for c in comments]
    evidence['independent_review'] = False
    if evidence.get('independent_review_comment'):
        independent = github('api', f'repos/clemarc/fava/issues/comments/{evidence["independent_review_comment"]}')
        if independent['issue_url'] == report['issue_url'] and independent['html_url'] == review:
            reviewed = json.loads(independent['body'])
            evidence['independent_review'] = bool(reviewed.get('reviewer') and reviewed.get('worker')
                                                 and reviewed['reviewer'] != reviewed['worker']
                                                 and reviewed.get('head') == head and reviewed.get('target') == target)
    elif evidence.get('independent_review_id'):
        independent = github('api', f'repos/clemarc/fava/pulls/{number}/reviews/{evidence["independent_review_id"]}')
        evidence['independent_review'] = bool(independent['html_url'] == review and independent['commit_id'] == head
                                             and independent['state'] != 'PENDING'
                                             and evidence.get('review_target') == target
                                             and independent['user']['login'] != evidence.get('worker_login'))
    # Semantic review, findings dispositions and native artifact interpretation
    # require coordinator inspection. Their linked reports are not AI CI gates.
    evidence['structural_drift'] = not errors
    if not ancestor(root, target, head):
        evidence['validated_target'] = None  # Required up-to-date integration policy.
    return evidence, evaluate(evidence)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('identifier')
    parser.add_argument('--pr', type=int, required=True)
    parser.add_argument('--evidence-comment', type=int, help='SHA-bound coordinator JSON PR comment, written after publication')
    args = parser.parse_args()
    try:
        evidence, errors = assess(Path.cwd(), args.identifier, args.pr, args.evidence_comment)
        print(json.dumps({'evidence': evidence, 'blockers': errors}, indent=2))
        raise SystemExit(bool(errors))
    except (ValueError, KeyError, subprocess.CalledProcessError) as error:
        parser.exit(1, f'STOP: {error}\n')


if __name__ == '__main__':
    main()
