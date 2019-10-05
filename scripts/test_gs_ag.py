#!/usr/bin/env python3
#
# test_gs_ag.py
#
# Tests Gradescope autograder configuration
#
# Author: Sreepathi Pai
#
# Copyright (C) 2019, Sreepathi Pai

import argparse
import zipfile
import tempfile
import os
import shutil
import subprocess
import json
from datetime import datetime, timedelta

def create_submission_metadata(p):
    smd = {'id': 1,
           'created_at': datetime.now().isoformat(),
           'assignment': {
               'due_date': (datetime.now() + timedelta(days=7)).isoformat(),
               'group_size': None,
               'group_submission': False,
               'id': 2,
               'course_id': 3,
               'late_due_date': None,
               'release_data': (datetime.now() - timedelta(days=1)).isoformat(),
               'title': 'Test Assignment',
               'total_points': "10.0",
               'submission_method': 'upload',
           },
           'users': [
               {
                   'email': 'benbitdiddle@example.com',
                   'id': 1,
                   'name': 'Ben Bitdiddle'
               }
           ],
           'previous_submissions': []
           }

    with open(os.path.join(p, 'submission_metadata.json'), 'w') as f:
        f.write(json.dumps(smd, indent=4))

if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Test autograder submission")
    p.add_argument("archive", help="Autograder archive file")
    p.add_argument("submission", help="Student submission" )

    args = p.parse_args()

    nd = tempfile.mkdtemp()
    print(nd)

    agd = os.path.join(nd, "autograder")

    srcd = os.path.join(agd, "source")
    subd = os.path.join(agd, "submission")
    resd = os.path.join(agd, "results")

    for i in [agd, srcd, subd, resd]:
        os.mkdir(i)

    # these destroy permissions
    #azip = zipfile.ZipFile(args.archive)
    #azip.extractall(srcd)

    #szip = zipfile.ZipFile(args.submission)
    #szip.extractall(subd)

    subprocess.check_call(['unzip', '-q', args.archive, '-d', srcd])
    subprocess.check_call(['unzip', '-q', args.submission, '-d', subd])

    shutil.copy(os.path.join(srcd, "run_autograder"), agd)

    create_submission_metadata(agd)

    os.chdir(agd)
    os.environ["AGROOT"] = nd
    print(f"Switching to {agd} with AGROOT={nd}. Type `exit` to quit. Directory will be deleted when process exits.")

    ret = os.spawnlp(os.P_WAIT, "bash", "bash", "-i")

    if ret == 0: # not sure why exit returns 1
        print(f"Removing {agd}")
        shutil.rmtree(nd)
    else:
        # you can reach here using `exit` in the shell or if the run_autograder script fails
        print(f"Return code={ret}, {agd} was not removed.")
