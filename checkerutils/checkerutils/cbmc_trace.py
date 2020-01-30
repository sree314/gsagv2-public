#!/usr/bin/env python3
#
# cbmc_trace.py
#
# Filter CBMC counter-example trace to limited set of values.
#
# Annotate the checker files with //@begin for each function that has
# a record. Use //@record before each line that you want to be
# recorded. Currently, only assignments are displayed.
#
# Author: Sreepathi Pai
#
# Copyright (C) 2019, Sreepathi Pai
#

import json
import argparse
import os
import sys

def get_record_locations(srcfile):
    lines={}
    func = None

    with open(srcfile, 'r') as f:
        for i, l in enumerate(f):
            ls = l.strip()
            if ls == '//@record':
                assert func is not None, "You must provide //@begin fn-name at the beginning of function"
                lines[func].append(i+2)
            elif '//@begin' in ls:
                func = ls.split()[-1]
                lines[func] = []

            if func and len(lines[func]) and (i+2) == lines[func][-1]:
                assert len(ls), "Line after //@record cannot be empty!"

    for k in lines:
        lines[k] = set(lines[k])

    return lines

class CBMCTrace(object):
    def __init__(self, jsond = None, jsonfile = None):
        assert jsond or jsonfile, "Must provide either json or jsonfile"
        assert jsond is None or jsonfile is None, "Must not provide both json or jsonfile"

        if jsond:
            self.json = jsond
        else:
            with open(jsonfile, "rb") as f:
                self.json = json.load(f)

        self._result = None

    def get_results(self, assert_on_missing = True):
        if not self._result:
            for x in self.json:
                if "result" in x:
                    self._result = x['result']
                    break
            else:
                if assert_on_missing:
                    assert False, "No result key found!"
                else:
                    self._result = []

        return self._result

    def get_errors(self):
        for x in self.json:
            if "messageType" in x and x["messageType"] == "ERROR":
                yield x

if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Parse CBMC JSON output")

    p.add_argument("jsonfile", help="JSON File")
    p.add_argument("srcfile", help="Source file for checker File")
    p.add_argument("outputjson", help="Output file containing results")

    args = p.parse_args()

    with open(args.jsonfile, "rb") as f:
        j = json.load(f)

    record_fn = get_record_locations(args.srcfile)

    if len(record_fn) == 0:
        print(f"WARNING: No //@begin and //@record found in {args.srcfile}", file=sys.stderr)

    srcfile = os.path.basename(args.srcfile)

    out = []
    ct = CBMCTrace(j)
    for r in ct.get_results():
        print(f"{r['property']}: {r['description']}: {r['status']}")

        test = {'property': r['property'],
                'description': r['description'],
                'status': r['status']}

        if r['status'] == "FAILURE":
            function_depth = 0
            function = []
            data = {}
            order = []

            if not 'trace' in r:
                continue

            for t in r['trace']:
                if t['hidden']:
                    continue

                if t['stepType'] == 'function-call':
                    function_depth += 1
                    function.append(t['function']['displayName'])

                if t['stepType'] == 'assignment' and t['assignmentType'] == 'variable':
                    show = False
                    if 'sourceLocation' in t and function[-1] in record_fn:
                        if t['sourceLocation']['file'] == srcfile:
                            if int(t['sourceLocation']['line']) in record_fn[function[-1]]:
                                show=True
                                ln = t['sourceLocation']['line']

                    if show:
                        if t['lhs'] not in data:
                            order.append(t['lhs'])

                        if 'data' in t['value']:
                            data[t['lhs']] = (t['value']['data'], t['value']['binary'])
                            #print(ln, t['lhs'], t['value']['data'])
                        else:
                            data[t['lhs']] = t['value']
                            #print(ln, t['lhs'], t['value'])

                if t['stepType'] == 'function-return':
                    function_depth -= 1
                    function.pop()

            counter_example = "\n".join([f"\t{k} = {data[k][0]} ({data[k][1]})" for k in order])
            test['output'] = counter_example

        out.append(test)

    with open(args.outputjson, "w") as f:
        f.write(json.dumps(out, indent=4))
