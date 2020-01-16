#!/usr/bin/env python3
#
# testhelper.py
#
# Parse and score test_helper.c output
#
# Author: Sreepathi Pai
#
# Copyright (c) 2019, 2020, Sreepathi Pai
#

import logging
import re

logger = logging.getLogger(__name__)
PASS_RE = re.compile("^PASS:")

class TestHelperScore(object):
    def __init__(self, max_score, total_results):
        self.max_score = max_score
        self.total_results = total_results
        assert self.total_results > 0

    def get_max_score(self):
        return '{0:0.2f}'.format(self.max_score)

    def _parse_th(self, th_file):
        with open(th_file, "r") as f:
            results = f.readlines()
            passes = []
            fails = []
            for l in results:
                if PASS_RE.match(l):
                    passes.append(l)
                else:
                    fails.append(l)

        self.results = results
        return passes, fails

    def score2(self, th_file, test):
        test.score = self.score(th_file)
        test.max_score = self.get_max_score()

    def score(self, th_file):
        passes, fails = self._parse_th(th_file)

        logger.info(f'record {th_file} contains {len(passes)} passes, {len(fails)} fails, with {self.total_results} total tests expected')

        if len(passes) == 0 and len(fails) == 0:
            logger.error(f"Note {th_file} contains no pass/fail data")
            return 0 # will grab attention

        if len(passes) + len(fails) > self.total_results:
            logger.error(f"Note {th_file} contains more than {self.total_results} results: {len(passes) + len(fails)} results found")
            return 0

        if len(passes) + len(fails) < self.total_results:
            logger.warning(f"Note {th_file} contains fewer than {self.total_results} results: {len(passes) + len(fails)} result(s) found")

        return "{0:0.2f}".format(len(passes)/self.total_results * self.max_score)
