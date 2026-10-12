"""Validate local skill discovery, guidance links and public-repository guardrails."""
import json
from pathlib import Path
import re


def validate(root):
    errors = []
    for path in root.glob('.agents/skills/*/SKILL.md'):
        text = path.read_text()
        if not text.startswith('---\n') or not re.search(r'^name:', text, re.M) or not re.search(r'^description:', text, re.M):
            errors.append(f'{path}: skill needs YAML name/description front matter')
    for file in ['AGENTS.md', '.agents/skills/fava-ci-verify/SKILL.md']:
        text = (root / file).read_text()
        for target in re.findall(r'`((?:docs/|\.agents/|\.specify/|\.github/|tools/)[^` *<>]+)`', text):
            if not (root / target).exists(): errors.append(f'{file}: missing reference {target}')
    workflows = sorted(path for path in root.glob('.github/workflows/*')
                       if path.is_file() and path.suffix in {'.yml', '.yaml'})
    for path in workflows:
        text = path.read_text()
        for action in re.findall(r'uses:\s*([^\s#]+)', text):
            if not action.startswith('./') and not re.search(r'@[0-9a-f]{40}$', action): errors.append(f'{path}: pin action {action} to a full SHA')
        if 'pull_request_target' in text or 'secrets:' in text: errors.append(f'{path}: privileged PR/secrets configuration needs separate review')
        if 'contents: read' not in text: errors.append(f'{path}: declare read-only contents permission')
    lock = json.loads((root / 'package-lock.json').read_text())
    if lock['packages']['']['devDependencies']['@schpet/linear-cli'] != json.loads((root / 'package.json').read_text())['devDependencies']['@schpet/linear-cli']:
        errors.append('Linear CLI package pin differs from lockfile')
    # Narrow high-confidence guards; review remains mandatory for private health data.
    for path in root.rglob('*'):
        if not path.is_file() or any(part in {'.git', 'node_modules', '__pycache__', 'artifacts'} for part in path.parts): continue
        if path.name == 'export.xml' or path.suffix.lower() in {'.p12', '.mobileprovision'}: errors.append(f'{path}: HealthKit export or signing credential must not be public')
        try: text = path.read_text()
        except (UnicodeError, OSError): continue
        patterns = [r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----', r'\bgh[pousr]_[A-Za-z0-9]{30,}', r'\bgithub_pat_[A-Za-z0-9_]{30,}', r'\blin_api_[A-Za-z0-9]{30,}']
        if any(re.search(p, text) for p in patterns): errors.append(f'{path}: potential credential; remove it and review exposure without printing contents')
    return errors


if __name__ == '__main__':
    errors = validate(Path.cwd())
    for error in errors: print('ERROR:', error)
    if errors: raise SystemExit(1)
    print('Tooling references, skill discovery and public-repository guardrails passed.')
