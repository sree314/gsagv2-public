#!/usr/bin/env python3
#
# gs.py
#
# Utilities to deal with Gradescope, mostly generating results.json
#
# Author: Sreepathi Pai
#
# Copyright (c) 2019, 2020, Sreepathi Pai

import json
import os
from pathlib import Path

# visibility for test cases
VIS_HIDDEN = "hidden" # never shown to students
VIS_AFTER_DUE_DATE = "after_due_date" # only after due date
VIS_AFTER_PUBLISHED = "after_published" # after explicitly published
VIS_VISIBLE = "visible" # default
VIS_DEFAULT = VIS_VISIBLE

VIS_VALID = {VIS_HIDDEN, VIS_AFTER_DUE_DATE, VIS_AFTER_PUBLISHED, VIS_VISIBLE}

# internal
STATUS_SUCCESS = 0
STATUS_FAIL = 1

def SuccessfulTest(t):
    t._status = STATUS_SUCCESS

def FailedTest(t):
    t._status = STATUS_FAIL

class GSEnv(object):
    """Gradescope environment"""
    def __init__(self, agroot = '/'):
        self.AUTOGRADER_PATH = Path(agroot) /  'autograder'
        self.SOURCE_PATH = self.AUTOGRADER_PATH / 'source'
        self.SUBMISSION_PATH = self.AUTOGRADER_PATH / 'submission'
        self.SUBMISSION_METADATA = self.AUTOGRADER_PATH / 'submission_metadata.json'
        self.RESULTS_PATH = self.AUTOGRADER_PATH / 'results'
        self.RESULTS_JSON = self.RESULTS_PATH / 'results.json'

class GSTest(object):
    """A test in the results.json file.

       TODO: Make this a generic test."""
    def __init__(self, name, score = None, max_score = None, number = None, output = ""):
        self.name = name
        self.score = score
        self.max_score = max_score
        self.number = number
        self.output = []
        self.tags = []
        self.visibility = None
        self.extra_data = dict()
        self._status = None
        if output != "": self.add_output(output)

    def success(self):
        return self._status == STATUS_SUCCESS

    def add_output(self, output):
        self.output.append(output)

    def add_tag(self, tag):
        self.tags.append(tag)

    def add_extra_data(self, key, value):
        self.extra_data[key] = value

    def to_dict(self):
        out = {}

        for a in ['name', 'score', 'max_score', 'number', 'output',
                  'tags', 'visibility', 'extra_data']:
            v = getattr(self, a)
            if v is not None:
                if a == 'output':
                    if len(v): out['output'] = "\n".join(v)
                elif a in ('tags', 'extra_data'):
                    if len(v): out[a] = v
                else:
                    out[a] = v

        return out

class GSResults(object):
    """Represents a results.json file

       TODO: Read a results.json file, so this can be incrementally modified."""

    execution_time = None # seconds
    score = None
    visibility = None
    stdout_visibility = None
    extra_data = None

    def __init__(self, jsonfile):
        self.jf = jsonfile
        self.output = []
        self.extra_data = dict()
        self.tests = []

    def add_output(self, t):
        """This is output at top of file"""
        self.output.append(t)

    def add_extra_data(self, key, value):
        self.extra_data[key] = value

    def add_test(self, t):
        self.tests.append(t)

    @property
    def last_test(self):
        return self.tests[-1]

    def add_leaderboard(self, l):
        raise NotImplementedError

    def get_results_json(self):
        d = self.to_dict()

        #TODO: check for errors in results.json file
        if 'score' not in d and 'tests' in d:
            for t in d['tests']:
                if 'score' not in t:
                    raise ValueError('results.json does not contain scores')

        # improve UI
        if 'tests' in d:
            for t in d['tests']:
                if 'visibility' in t and t['visibility'] != VIS_VISIBLE:
                    v = t['visibility']

                    if v == VIS_AFTER_DUE_DATE:
                        v = "After Due Date"
                    elif v == VIS_AFTER_PUBLISHED:
                        v = "After Published"
                    elif v == VIS_HIDDEN:
                        v = "Hidden"

                    t['name'] = t['name'] + f"(Visibility: {v})"

        return json.dumps(d, indent=4)

    def to_dict(self):
        out = {}

        for a in ['execution_time', 'score', 'visibility', 'stdout_visibility',
                  'extra_data', 'tests', 'output']:
            v = getattr(self, a)
            if v is not None:
                if a == 'output':
                     if len(v) > 0: out['output'] = "\n".join(v)
                elif a == 'extra_data':
                    if len(v) > 0: out[a] = v
                elif a == 'tests':
                    if len(v) > 0:
                        out[a] = [x.to_dict() for x in v]
                        if any([len(x) == 0 for x in out[a]]):
                            # this is valid since all fields in test are
                            # optional, but almost certainly not what you
                            # want
                            raise ValueError("Some tests are empty")
                else:
                    out[a] = v

        return out

    def write(self):
        with open(self.jf, "w") as f:
            f.write(self.get_results_json())

class PropDict(object):
    def from_dict(self, d):
        for k, v in d.items():
            setattr(self, k, v)

        return self

class GSAssignment(PropDict):
    pass

class GSUser(PropDict):
    pass

class GSPreviousSubmission(PropDict):
    pass

class GSSubmissionMetadata(object):
    def __init__(self, gsenv):
        self.jf = Path(gsenv.SUBMISSION_METADATA)

    def read(self):
        with open(self.jf, "r") as f:
            self._json = json.load(f)

        self.assignment = GSAssignment().from_dict(self._json['assignment'])
        self.users = [GSUser().from_dict(x) for x in self._json['users']]

        # TODO: convert previous submissions 'results' into GSResults?
        self.previous_submissions = [GSPreviousSubmission().from_dict(x) for x in self._json['previous_submissions']]

        for x in ['id', 'created_at']:
            setattr(self, x, self._json[x])
