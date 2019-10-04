#!/usr/bin/env python3

import argparse
import yaml
import os
import json

if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Generate a results.json for Gradescope")
    p.add_argument("assignmentyaml", help="Assignment YAML file")
    p.add_argument("cbmc_results_json", nargs="+", help="JSON files produced by cbmc_trace.py")

    args = p.parse_args()

    cbmc_results = []
    for x in args.cbmc_results_json:
        with open(x, "rb") as f:
            cbmc_results.extend(json.load(f))

    if not os.path.exists(args.assignmentyaml):
        print(f"WARNING: {args.assignmentyaml} does not exist, creating template, no results.json will be produced")
        out = {'properties': {}}
        for i, p in enumerate(cbmc_results):
            # ignore plain asserts
            ign = False
            if p['description'][:10] == "assertion ": ign = True

            out['properties'][p['property']] = {'description': p['description'],
                                                'score': 0, 'ignore': ign,
                                                'order': i}
        with open(args.assignmentyaml, "w") as f:
            f.write(yaml.dump(out))
    else:
        with open(args.assignmentyaml, "r") as f:
            ay = yaml.load(f.read())

    tests = []

    for r in cbmc_results:
        p = r['property']
        if p not in ay['properties']:
            print(f"UNKNOWN {p}, skipping, add to {args.assignmentyaml} if needed")
            continue

        ayp = ay['properties'][p]

        if ayp['ignore']:
            print(f"IGNORING {p}")
            continue

        t = {}
        t['name'] = f"{p}: {r['description']}"

        if 'order' in ayp:
            t['number'] = ayp['order']

        t['max_score'] = ayp['score']

        if r['status'] == 'SUCCESS':
            t['score'] = ayp['score']
        else:
            t['score'] = 0
            t['output'] = r['output']

        tests.append(t)

    results = {'tests': tests}

    with open("results.json", "w") as f:
        f.write(json.dumps(results, indent=4))
