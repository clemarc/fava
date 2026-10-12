"""Prepare a createCommitOnBranch request from the Git index; no network writes."""

import argparse
import base64
import json
import os
from pathlib import Path
import re
import subprocess


def git(*args):
    return subprocess.check_output(["git", *args])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True, help="GitHub owner/name")
    parser.add_argument("--branch", required=True, help="Existing destination branch")
    parser.add_argument("--parent", required=True, help="Expected destination HEAD SHA")
    parser.add_argument("--message-file", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path, help="New JSON file, preferably in /tmp")
    args = parser.parse_args()

    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", args.repository):
        parser.error("repository must be owner/name")
    subprocess.run(["git", "check-ref-format", "--branch", args.branch], check=True, stdout=subprocess.DEVNULL)
    if not re.fullmatch(r"[0-9a-f]{40}", args.parent):
        parser.error("parent must be a full SHA-1 commit ID")
    git("cat-file", "-e", args.parent + "^{commit}")
    if git("ls-files", "--unmerged"):
        parser.error("resolve index conflicts before preparing a commit")

    message = args.message_file.read_text().strip()
    if not message:
        parser.error("commit message cannot be empty")
    headline, _, body = message.partition("\n")

    additions, deletions = [], []
    entries = git("diff", "--cached", "--raw", "-z", "--no-renames", "--no-abbrev", args.parent, "--").split(b"\0")
    for index in range(0, len(entries) - 1, 2):
        metadata = entries[index].decode("ascii").split()
        path = entries[index + 1].decode("utf-8")
        old_mode, new_mode, _, blob, status = metadata
        old_mode = old_mode.removeprefix(":")
        # GraphQL FileAddition cannot represent executable bits, symlinks,
        # or submodules. Do not silently flatten existing file modes.
        if old_mode not in {"000000", "100644"} or new_mode not in {"000000", "100644"}:
            parser.error(f"GraphQL cannot preserve the changed file mode: {path}")
        if status == "D":
            deletions.append({"path": path})
        elif status in {"A", "M"}:
            contents = base64.b64encode(git("cat-file", "blob", blob)).decode("ascii")
            additions.append({"path": path, "contents": contents})
        else:
            parser.error(f"unsupported index change {status}: {path}")

    if not additions and not deletions:
        parser.error("no staged changes relative to the expected parent")
    query = Path(__file__).with_name("create-commit-on-branch.graphql").read_text()
    request = {
        "query": query,
        "variables": {
            "input": {
                "branch": {"repositoryNameWithOwner": args.repository, "refName": args.branch},
                "expectedHeadOid": args.parent,
                "message": {"headline": headline, "body": body.strip()},
                "fileChanges": {"additions": additions, "deletions": deletions},
            }
        },
    }
    # Use an exclusive, private file: never overwrite a reviewer's request.
    descriptor = os.open(args.output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "w") as stream:
        json.dump(request, stream, indent=2)
        stream.write("\n")
    print(f"Prepared {len(additions)} additions/updates and {len(deletions)} deletions in {args.output}")


if __name__ == "__main__":
    main()
