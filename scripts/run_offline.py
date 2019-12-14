#!/usr/bin/env python3
#
# run_offline.py
#
# Runs offline tests
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
import yaml
import glob

def smd_dummy():
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
    return smd

def smd_from_export(smd_export, submission_id):
    smd = {'id': submission_id,
           'created_at': smd_export[':created_at'].isoformat(),
           'assignment': {
               'due_date': (smd_export[':created_at'] + timedelta(days=7)).isoformat(),
               'group_size': None,
               'group_submission': False,
               'id': 2,
               'course_id': 3,
               'late_due_date': None,
               'release_date': (datetime.now() - timedelta(days=1)).isoformat(),
               'title': 'Test Assignment',
               'total_points': "10.0",
               'submission_method': 'upload',
           },
           'users': [],
           'previous_submissions': []
    }

    for n in smd_export[':submitters']:
        smd['users'].append({'email': n[':email'],
                             'name': n[':name'],
                             'id': n[':sid']})

    #TODO: previous submission

    return smd

def create_autograder_env(archive, submission, metadata):
    nd = tempfile.mkdtemp()

    agd = os.path.join(nd, "autograder")

    srcd = os.path.join(agd, "source")
    subd = os.path.join(agd, "submission")
    resd = os.path.join(agd, "results")

    for i in [agd, srcd, subd, resd]:
        os.mkdir(i)

    subprocess.check_call(['unzip', '-q', archive, '-d', srcd])
    subprocess.check_call(['unzip', '-q', submission, '-d', subd])

    shutil.copy(os.path.join(srcd, "run_autograder"), agd)

    create_submission_metadata(metadata, agd)

    return nd

def create_submission_metadata(smd, p):
    with open(os.path.join(p, 'submission_metadata.json'), 'w') as f:
        f.write(json.dumps(smd, indent=4))

def get_submission_metadata_yaml(json_smd):
    myaml = {}
    myaml[':id'] = json_smd['id']

    return yaml.dump(myaml)

def update_autograder_offline(nd):
    agd = os.path.join(nd, "autograder")
    os.chdir(agd)
    os.environ["AGROOT"] = nd
    subprocess.check_call(["source/update.sh"])

def run_autograder(nd):
    agd = os.path.join(nd, "autograder")
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

def run_autograder_offline(nd, offlined):
    agd = os.path.join(nd, "autograder")
    os.chdir(agd)
    os.environ["AGROOT"] = nd
    os.environ["OFFLINE_AUTOGRADER"] = "1"
    os.environ["OFFLINE_PATH"] = offlined

    print(f"Switching to {agd} with AGROOT={nd}. Type `exit` to quit. Directory will be deleted when process exits.")

    ret = os.spawnlp(os.P_WAIT, "bash", "bash", "-i")

    if ret == 0: # not sure why exit returns 1
        print(f"Removing {agd}")
        shutil.rmtree(nd)
    else:
        # you can reach here using `exit` in the shell or if the run_autograder script fails
        print(f"Return code={ret}, {agd} was not removed.")

def get_export_submissions_md(exportdir):
    if os.path.exists(os.path.join(exportdir, "submission_metadata_lite.yml")):
        fn = os.path.join(exportdir, "submission_metadata_lite.yml")
        lite = True
    else:
        fn = os.path.join(exportdir, "submission_metadata.yml")
        lite = False

    with open(fn) as f:
        smd = yaml.safe_load(f)
        return smd, lite

def gen_light_smd(smd, exportdir):
    def clean_results(r):
        if 'tests' not in r:
            return

        for t in r['tests']:
            if 'output' not in t:
                # already light?
                return
            else:
                del t['output']

    for s in smd:
        if ':history' in smd[s]:
            for hs in smd[s][':history']:
                 if ':results' in hs:
                     clean_results(hs[':results'])

        if ':results' in smd[s] :
            clean_results(smd[s][':results'])

        with open(os.path.join(exportdir, "submission_metadata_lite.yml"), "w") as f:
            yaml.safe_dump(smd, f)

def repack_export_submission(exportdir, subid, json_smd, output = None):
    if output is None:
        h, output = tempfile.mkstemp(suffix=".zip")
        os.close(h)
        os.unlink(output)

    md = get_submission_metadata_yaml(json_smd)
    with zipfile.ZipFile(output, 'x') as z:
        subdir = os.path.join(exportdir, f"submission_{subid}")
        files = glob.glob(subdir + "/**", recursive=True)

        for f in files:
            arcname = os.path.relpath(f, start=subdir)
            if arcname == ".":
                continue

            print(f"\tadding {f}")
            z.write(f, arcname=arcname)

        z.writestr('metadata.yml', md)

    return output

if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Run offline tests on submissions")
    p.add_argument("archive", help="Autograder archive file")
    p.add_argument("exportdir", help="Gradescope submission export archive directory") #need to change this to be more general?
    p.add_argument("offlinedir", help="Directory to store offline results")
    p.add_argument("submission_id", nargs="*", help="Submissions to test")

    args = p.parse_args()

    smd, lite = get_export_submissions_md(args.exportdir)
    if not lite:
        print("generating lite version")
        gen_light_smd(smd, args.exportdir)

    submission_ids = [k[len('submission_'):] for k in smd.keys()]
    print(f"{len(submission_ids)} submissions found")
    if not len(args.submission_id):
        args.submission_id = submission_ids

    for sid in args.submission_id:
        md = smd[f'submission_{sid}']
        jsonmd = smd_from_export(md, int(sid))
        submission = repack_export_submission(args.exportdir, sid, jsonmd)

        nd = create_autograder_env(args.archive, submission, jsonmd)
        print(f"Autograder environment created in {nd}")
        update_autograder_offline(nd)
        run_autograder_offline(nd, args.offlinedir)
        break
