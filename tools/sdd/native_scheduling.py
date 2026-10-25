"""Default-off native scheduling; never changes applicability or acceptance gates."""
from datetime import datetime
import json
import re
import subprocess

import milestone
from ledger import target_import, task_publication_progress
from signatures import verify


def full(reason):
    return dict(acceptance=True, compile_feedback=False, reason=reason)


def decide(root, event, git=milestone.git, signed=verify, progress=task_publication_progress):
    """Only proven initial publications may defer; uncertainty runs full native."""
    try:
        pr = event.get('pull_request')
        if not isinstance(pr, dict):
            return full('not_a_task_pull_request')
        repository = event['repository']['full_name']
        if repository != 'clemarc/fava' or pr['head']['repo']['full_name'] != repository:
            return full('not_same_repository')
        base, branch = pr['base']['ref'], pr['head']['ref']
        match = re.fullmatch(r'milestone/(r[1-9][0-9]*(?:\.[1-9][0-9]*)?)', base)
        if not match or not branch.startswith('task/' + match[1] + '/'):
            return full('outside_registered_task_branch_pattern')
        target, head, number = pr['base']['sha'], pr['head']['sha'], pr['number']
        if (type(number) is not int or number < 1 or
                any(not isinstance(s, str) or not re.fullmatch('[0-9a-f]{40}', s) for s in (target, head))
                or git(root, 'rev-parse', 'HEAD').strip() != head):
            return full('inconsistent_event_checkout_identity')
        # A candidate cannot activate itself: read the event target's config.
        config = json.loads(git(root, 'show', target + ':.github/native-scheduling.json'))
        if (set(config) != {'schema', 'enabled_milestones'} or config['schema'] != 1
                or not isinstance(config['enabled_milestones'], list)
                or match[1].upper() not in config['enabled_milestones']):
            return full('pilot_disabled_on_target')
        paths = git(root, 'ls-tree', '-r', '--name-only', target).splitlines()
        resolved = milestone.resolve(match[1], {p:git(root, 'show', target + ':' + p)
                                               for p in paths if p.endswith('/roadmap.md')})
        canonical = json.loads(git(root, 'show', target + ':' + resolved['ledger']))
        if canonical.get('milestone_branch') != base or canonical.get('milestone') != resolved['id']:
            return full('canonical_milestone_identity_invalid')
        record = canonical.get('task_prs', {}).get(str(number))
        # Strip only signed pure automatic target imports to find the source
        # publication. A corrective/non-import source head always runs native.
        source = head
        imports = []
        while True:
            imported, errors = target_import(root, source, target, git)
            if errors:
                return full('invalid_pure_import')
            if not imported:
                break
            if not signed(root, source):
                return full('unverified_import_signature')
            imports.append(source)
            source = git(root, 'show', '-s', '--format=%P', source).split()[0]
        opened = datetime.fromisoformat(pr['created_at'].replace('Z', '+00:00'))
        published = datetime.fromisoformat(git(root, 'show', '-s', '--format=%cI', source).strip())
        if opened.tzinfo is None or published.tzinfo is None or published >= opened:
            return full('post_opening_or_ambiguous_source_head')
        if not signed(root, source):
            return full('unverified_initial_source_signature')
        if record:
            if (record.get('branch') != branch or record.get('heads', [None])[0] != source
                    or not record.get('tasks') or record.get('correction_cycles') != 0):
                return full('corrective_or_inconsistent_registration')
            state = progress(root, target, head, resolved['ledger'], number, pr['created_at'], git)
            registration = state.get('reservations', {}).get(0)
            if not registration or not signed(root, registration):
                return full('canonical_registration_not_verified')
            carried = False
            try:
                git(root, 'merge-base', '--is-ancestor', registration, head)
                local = json.loads(git(root, 'show', head + ':' + resolved['ledger']))
                carried = local.get('task_prs', {}).get(str(number)) == record
            except subprocess.CalledProcessError:
                pass
            if carried and imports:
                return full('canonical_registration_import_verified')
        return dict(acceptance=False, compile_feedback=True,
                    reason='initial_source_awaiting_canonical_registration_import')
    except (ValueError, KeyError, TypeError, AttributeError, IndexError, OSError, subprocess.SubprocessError):
        return full('scheduling_evidence_unavailable_run_full_native')
