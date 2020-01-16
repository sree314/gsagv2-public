#!/usr/bin/env python3

import logging

from checkerutils import runner, gs

logger = logging.getLogger(__name__)

ZIP_ROOT = 'aX' # CHANGE THIS TO DIRECTORY INSIDE SUBMITTED ZIP

# use static methods to discourage state outside of env
class Checker(object):
    @staticmethod
    def init_results(env):
        env.results.score = 0
        env.CHK_ASGN_PATH = env.SUBMISSION_PATH / ZIP_ROOT

    @staticmethod
    def sanity_checks(env):
        """Perform any sanity checks here"""
        return True

    @staticmethod
    def prepare(env):
        """Perform the submission directory for testing, usually by copying files, tests, etc."""
        return True

    @staticmethod
    def check(env):
        return True

def get_checker(env):
    return Checker
