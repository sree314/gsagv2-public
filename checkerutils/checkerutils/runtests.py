#!/usr/bin/env python3
#
# runtests.py
#
# Utilities for running tests, and displaying their output in gradescope tests.
#
# Author: Sreepathi Pai
#
# Copyright (c) 2020, Sreepathi Pai

import tempfile
import os
import cbmc_trace
import types
import runner

def get_temp_file(suffix=None,prefix=None,dir=None,text=False,close=True):
    h, n = tempfile.mkstemp(suffix=suffix, prefix=prefix,dir=dir,text=text)
    if close:
        os.close(h)
        return n
    else:
        return h, n

def cbmc_debug_output(self):
    cj = cbmc_trace.CBMCTrace(jsonfile=self.args['json'])

    out = []
    for e in cj.get_errors():
        out.append(f"    ERROR: {e['messageText']}")

    for r in cj.get_results(assert_on_missing=False):
        out.append(f"    {r['status']}: {r['description']}")

    return "\n".join(out)

class RunTest(object):
    # """RunTest takes a run_result (from runner.py) and converts it to a
    #    PASS/FAIL test in Gradescope.

    #    Along the way, it can check for internal errors in the test and
    #    suppress output/alert users if needed.
    # """

    max_output = 4096 # output bigger than this will be "shortened", keep it at 0 to allow unlimited

    def __init__(self, test, sub_test_title, run_result,
                 internal_error = None, debug_output = None, args = None):
        self.rr = run_result
        self.stt = sub_test_title
        self.test = test  # gradescope-style test
        self.args = args

        if internal_error is not None: self.internal_error = types.MethodType(internal_error, self)
        if debug_output is not None: self.debug_output = types.MethodType(debug_output, self)

    def internal_error(self):
        # """Returns true if there seems to be an internal error.

        #    Ideally, there is a marker that indicates success, and if
        #    it is missing, we can assume internal error.
        # """

        # by default there are no internal errors
        return False

    def debug_output(self):
#        """Return output to be shown to the user when a test fails."""
        return self.rr.errors

    def process(self):
        if self.rr.success:
            self.test.add_output(f'PASS: {self.stt}')
            # maybe add success output?
            return True
        else:
            out = runner.shorten(self.rr.output, self.max_output)
            err = runner.shorten(self.rr.errors, self.max_output)
            if self.internal_error():
                logger.error(f'Internal error on {self.stt}')
                logger.error("STDOUT\n"+out)
                logger.error("STDERR\n"+err)

                self.test.add_output(f'FAIL: {self.stt}: Internal Error, please contact instructor')
            else:
                logger.error(f'Test failed: {self.stt}')
                logger.error("STDOUT\n"+out)
                logger.error("STDERR\n"+err)

                self.test.add_output(f'FAIL: {self.stt}')
                do = self.debug_output()
                if do: self.test.add_output(do)

            return False


if __name__ == "__main__":
    import gs

    t = RunTest(gs.GSTest("Test"), "Some tests", runner.run(['true']))
