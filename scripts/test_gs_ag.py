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
