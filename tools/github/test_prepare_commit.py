import base64
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

BUILDER = str(Path(__file__).with_name('prepare-commit.py').resolve())


class CommitRequestTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.git('init', '-q')
        self.git('config', 'user.name', 'Fixture')
        self.git('config', 'user.email', 'fixture@example.invalid')
        (self.root / 'old.txt').write_text('original\n')
        self.git('add', 'old.txt')
        self.git('-c', 'commit.gpgsign=false', 'commit', '-qm', 'fixture parent')
        self.parent = self.git('rev-parse', 'HEAD').stdout.strip()
        (self.root / 'message.txt').write_text('chore: fixture request\n\nTask: T014\n')

    def tearDown(self):
        self.temp.cleanup()

    def git(self, *args):
        return subprocess.run(['git', *args], cwd=self.root, check=True, capture_output=True, text=True)

    def build(self):
        return subprocess.run(['python3', BUILDER,
            '--repository', 'clemarc/fava', '--branch', 'chore/test',
            '--parent', self.parent, '--message-file', str(self.root / 'message.txt'),
            '--output', str(self.root / 'request.json')], cwd=self.root, capture_output=True, text=True)

    def test_exact_index_bytes_deletion_and_unstaged_exclusion(self):
        name = 'spaces and\nnewline.bin'
        staged = bytes(range(256))
        (self.root / name).write_bytes(staged)
        self.git('rm', '-q', 'old.txt')
        self.git('add', name)
        (self.root / name).write_bytes(b'unstaged replacement')
        (self.root / 'untracked.txt').write_text('excluded')
        result = self.build()
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads((self.root / 'request.json').read_text())
        request = payload['variables']['input']
        self.assertEqual(request['branch'], {
            'repositoryNameWithOwner': 'clemarc/fava', 'branchName': 'chore/test'})
        self.assertEqual(request['expectedHeadOid'], self.parent)
        self.assertEqual(request['message'], {'headline': 'chore: fixture request', 'body': 'Task: T014'})
        self.assertEqual(request['fileChanges']['deletions'], [{'path': 'old.txt'}])
        added = request['fileChanges']['additions']
        self.assertEqual(len(added), 1)
        self.assertEqual(added[0]['path'], name)
        self.assertEqual(base64.b64decode(added[0]['contents']), staged)
        self.assertEqual((self.root / 'request.json').stat().st_mode & 0o777, 0o600)
        self.assertIn('wasSignedByGitHub', payload['query'])
        self.assertEqual(self.git('rev-parse', 'HEAD').stdout.strip(), self.parent)

    def test_executable_mode_is_rejected(self):
        (self.root / 'run.sh').write_text('#!/bin/sh\nexit 0\n')
        (self.root / 'run.sh').chmod(0o755)
        self.git('add', 'run.sh')
        result = self.build()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('cannot preserve', result.stderr)
        self.assertFalse((self.root / 'request.json').exists())

    def test_symlink_is_rejected(self):
        (self.root / 'link').symlink_to('old.txt')
        self.git('add', 'link')
        result = self.build()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('cannot preserve', result.stderr)

    def test_existing_request_is_not_overwritten(self):
        (self.root / 'old.txt').write_text('changed')
        self.git('add', 'old.txt')
        (self.root / 'request.json').write_text('reviewed request')
        result = self.build()
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual((self.root / 'request.json').read_text(), 'reviewed request')

    def test_no_change_is_rejected(self):
        result = self.build()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('no staged changes', result.stderr)


if __name__ == '__main__':
    unittest.main()
