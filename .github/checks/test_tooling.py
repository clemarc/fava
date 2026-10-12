"""Security guard regressions using synthetic fixtures only."""
import json
from pathlib import Path
import tempfile
import unittest

import tooling


class ToolingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.put('AGENTS.md', 'Fixture guidance\n')
        self.put('.agents/skills/fava-ci-verify/SKILL.md',
                 '---\nname: fava-ci-verify\ndescription: Fixture skill\n---\n')
        dependencies = {'@schpet/linear-cli': '3.0.0'}
        self.put('package.json', json.dumps({'devDependencies': dependencies}))
        self.put('package-lock.json', json.dumps({
            'packages': {'': {'devDependencies': dependencies}}}))

    def put(self, name, text):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)

    def test_safe_fixture_and_documented_token_placeholder(self):
        self.put('README.md', 'Never publish github_pat_... or ${GITHUB_TOKEN}.\n')
        self.assertEqual(tooling.validate(self.root), [])

    def test_fine_grained_token_is_rejected_without_disclosure(self):
        # Construct a fake token at runtime so the regression fixture itself
        # contains no contiguous token-shaped string in public source/history.
        token = 'github_' + 'pat_' + 'A' * 22 + '_' + 'B' * 59
        self.put('config.txt', 'credential = ' + token + '\n')
        errors = tooling.validate(self.root)
        self.assertTrue(any('config.txt' in e and 'potential credential' in e
                            for e in errors))
        self.assertNotIn(token, '\n'.join(errors))

    def test_classic_token_detection_is_preserved(self):
        token = 'gh' + 'p_' + 'A' * 36
        self.put('config.txt', token)
        self.assertTrue(any('potential credential' in e
                            for e in tooling.validate(self.root)))

    def test_valid_workflows_with_both_extensions(self):
        for extension in ['yml', 'yaml']:
            self.put('.github/workflows/safe.' + extension,
                     'permissions:\n  contents: read\nsteps:\n'
                     '  - uses: actions/checkout@' + 'a' * 40 + '\n')
        self.assertEqual(tooling.validate(self.root), [])

    def test_both_extensions_enforce_each_workflow_guard(self):
        safe = 'permissions:\n  contents: read\n'
        cases = [
            (safe + 'uses: actions/checkout@v4\n', 'pin action'),
            (safe + 'on: pull_request_target\n', 'privileged PR/secrets'),
            (safe + 'secrets: inherit\n', 'privileged PR/secrets'),
            ('permissions:\n  contents: write\n', 'read-only contents'),
        ]
        for extension in ['yml', 'yaml']:
            name = '.github/workflows/unsafe.' + extension
            for text, expected in cases:
                with self.subTest(extension=extension, guard=expected, text=text):
                    self.put(name, text)
                    self.assertTrue(any(name in e and expected in e
                                        for e in tooling.validate(self.root)))
            (self.root / name).unlink()


if __name__ == '__main__':
    unittest.main()
