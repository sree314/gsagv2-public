#!/usr/bin/env python3
#
# runner.py
#
# Tools to run an external command.
#
# Author: Sreepathi Pai
#
# Copyright (c) 2019, 2020, Sreepathi Pai

import subprocess
import logging
from collections import namedtuple

MAX_OUTPUT = 0
logger = logging.getLogger(__name__)

RunResult = namedtuple('RUN_RESULT', 'success returncode output exception processobj outfile errfile')

def shorten(output):
    if MAX_OUTPUT == 0:
        return output

    if len(output) > MAX_OUTPUT:
        return "*** PARTIAL OUTPUT ***\n" + output[-MAX_OUTPUT:]

    return output

def safe_read(f):
    with open(f, "rb") as h:
        if MAX_OUTPUT == 0:
            return h.read()
        else:
            return h.read(MAX_OUTPUT)

def run(cmd, *args, **kwargs):
    assert type(cmd) is not str

    command = " ".join(cmd)

    hout = None
    herr = None

    try:
        if 'stdin' not in kwargs:
            kwargs['stdin'] = subprocess.DEVNULL

        outfile = None
        errfile = None

        if 'stdout' not in kwargs:
            hout, outfile = tempfile.mkstemp()
            kwargs['stdout'] = hout

        if 'stderr' not in kwargs:
            herr, errfile = tempfile.mkstemp()
            kwargs['stderr'] = herr

        if 'cwd' in kwargs:
            logging.info(f'Running {command} in {kwargs["cwd"]}')
        else:
            logging.info(f'Running {command}')

        process = subprocess.run(cmd, *args, **kwargs)
        if process.returncode == 0:
            logging.info(f'Running {command} succeeded')
        else:
            logger.error(f'Error when running "{command}", return code={process.returncode}')

        if hout: output = safe_read(outfile).decode('utf-8')
        if herr: errors = safe_read(errfile).decode('utf-8')

        return RunResult(success = process.returncode == 0,
                         returncode=process.returncode,
                         output=output,
                         processobj=process,
                         errors=errors,
                         outfile=outfile,
                         errfile=errfile,
                         exception=None)
    except Exception as e:
        logger.error(f'Error when running "{command}"', exc_info = e)
        return RunResult(success = False, returncode=None, output=None, exception=e,
                         processobj=None,errors=None,outfile=None,errfile=None)
    finally:
        if hout:
            os.close(hout)
            os.unlink(outfile)

        if herr:
            os.close(herr)
            os.unlink(errfile)

    assert False

def run_timeout(timeout_s, cmd, *args, **kwargs):
    command = ['timeout', f'{timeout_s}s'] + cmd
    logger.info(f"Running {command}")
    x = run(command, *args, **kwargs)
    if x.returncode == 124:
        x.output = x.output + "*** TIMEOUT ***\n"

    return x
