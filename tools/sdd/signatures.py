"""Offline verification with the pinned public GitHub web-flow signing key."""
import os
from pathlib import Path
import subprocess
import tempfile
try:
    from metrics import immutable_object
except ModuleNotFoundError:
    # Standalone callers (including the preflight's explicit pinned-verifier
    # loader) have no invocation context or tools/sdd import path.
    def immutable_object(kind, identity):
        pass

KEY = Path(__file__).with_name('github-web-flow.asc')
FINGERPRINT = '968479A1AFF927E37D1A566BB5690EEEBB952194'
OWNER_EMAIL = 'clmntlmrc@gmail.com'


def verify(root, sha):
    immutable_object('offline_signature', sha)
    # No private key, network lookup, developer keyring or persisted trust state.
    with tempfile.TemporaryDirectory(prefix='fava-public-key-') as directory:
        env = dict(os.environ, GNUPGHOME=directory)
        imported = subprocess.run(['gpg', '--batch', '--no-autostart', '--import', str(KEY)],
                                  env=env, capture_output=True)
        if imported.returncode:
            return False
        result = subprocess.run(['git', '-C', str(root), '-c', 'gpg.program=gpg',
                                 '-c', 'gpg.format=openpgp', 'verify-commit', '--raw', sha],
                                env=env, capture_output=True, text=True)
        return result.returncode == 0 and ('[GNUPG:] VALIDSIG ' + FINGERPRINT + ' ') in result.stderr


def owner_merge(root, sha, git):
    parents = git(root, 'show', '-s', '--format=%P', sha).split()
    return (len(parents) == 2
            and git(root, 'show', '-s', '--format=%ae', sha).strip() == OWNER_EMAIL
            and verify(root, sha))
