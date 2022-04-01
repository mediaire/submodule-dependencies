import re
import os
import subprocess
import sys

"""
Performs a check and only exits successfully (exit code 0) if all the
submodules in the folder are pointing to a valid version tag. It also exits
successfully if there are no submodules.

A "good" version is one that follows [_Semantic Versioning_ (SemVer)][semver],
i.e., `x.y.z`.

If the environment variable `ALLOW_DIRTY_SUBMODULES` is defined, it always
returns exits with code 0.
"""

COMMAND = """
/bin/bash -c "paste -d ' ' <(git submodule status | cut -d'(' -f1) <(git submodule foreach git describe --tags | grep -v 'Entering')"
"""

if __name__ == '__main__':
    out = subprocess.check_output(COMMAND, shell=True)
    invalid_refs = 0

    if os.environ.get('ALLOW_DIRTY_SUBMODULES'):
        print('Allowing dirty submodules - no check to be performed')
        sys.exit(0)

    for line in out.decode('utf-8').splitlines():
        splitted = line.split()
        if len(splitted) == 3:
            subproject = splitted[1]
            at_version = splitted[2].strip()
            print(f'{subproject} is at version {at_version}')
            if re.match('^\d+\.\d+\.\d+$', at_version):
                print('- good version tag')
            else:
                print('- NOT a good version tag')
                invalid_refs += 1

    print(f'There are {invalid_refs} invalid refs')
    sys.exit(0 if invalid_refs == 0 else 1)
