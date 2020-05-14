# checkerutils

Utilities to help writing checkers for autograders. If you use scripts
for building the autograder, you can `import checkerutils` in your
autograder to access the utilities briefly described below.

## gs.py

Utilities to parse Gradescope-specific data/JSON files, as well as
produce `results.json`.

## runner.py, runtests.py

`runner.py` is a low-level convenience wrapper over Python's
`subprocess` module. It can run commands with or without timeouts,
redirect input and capture output reliably, and detect errors.

`runtests.py` is meant to interface with specially-written external
checkers that follow certain conventions. It uses `runner.py` to
actually run these external checkers, but also parses their output to
display in the Gradescope UI. It can detect internal errors and alert
students to contact the instructor when this external checker
fails. An example of such a checker is `check_cbmc.py`.

## check_cbmc.py, cbmc_trace.py, cxform.py

`check_cbmc.py` is a tool to run the [C Bounded Model Checker](https://www.cprover.org/cbmc) on student-submitted C code. It takes the
provided C code, applies a number of transformations as dictated by an
instructor-provided YAML file (implemented by `cxform.py`) and uses
`cbmc_trace.py` to interpret CBMC output.

These tools are still incomplete.

## testhelper

This is a parser and scorer for the `test_helper.c` library that can
be used to record results of tests written in C.
