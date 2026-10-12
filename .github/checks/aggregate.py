"""Fail closed on cancelled, missing or unexpected mandatory job outcomes."""
import argparse


def validate(sdd, tooling, changes, native, state):
    if (sdd, tooling, changes) != ('success', 'success', 'success'): return False
    if state == 'required': return native == 'success'
    if state in {'onboarding', 'documentation'}: return native == 'skipped'
    return False


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ['sdd', 'tooling', 'changes', 'native', 'state']: parser.add_argument('--' + key, required=True)
    args = parser.parse_args()
    print('Required job outcomes:', vars(args))
    if not validate(**vars(args)): raise SystemExit('Required CI failed: inspect failed/cancelled/missing jobs or native applicability.')
    print('Applicable CI gates passed. A skipped native job provides no build/test evidence.')
