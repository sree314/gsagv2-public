# Gradescope Autograder

This is a collection of scripts to build a Gradescope-compatible
autograder.


## Create the assignment checker repository

Run `new_assignment.sh` to create an initial assignment checker git
repository. This will contain the scripts that check the assignments
for correctness.

```
$ ./new_assignment.sh /path/to/a1
```

By convention, the name `a1` is the same as the root directory inside
the zip that will ultimately be submitted by students. If you use a
different convention, change `ZIP_ROOT` in `checker.py` to reflect it.

Now, `/path/to/a1` will contain the following files in a newly
initialized git repository:

```
checker.py
checkerutils/
run_checker
setup_assignment.sh
ssh/
```

The file `checker.py` contains the actual tests to be run. It is
loaded, and executed by `run_checker`.

The file `setup_assignment.sh` contains commands to customize the
Docker image, such as installing packages specifically for this
assignment. It is sourced by `setup.sh`.

Before uploading to Gradescope (see instructions below), at the
minimum you should modify `setup_assignment.sh` if needed.

Create a repository on GitHub for the assignment, and push this
repository to it:

```
$ git remote set-url [url]
$ git push
```

The file `ssh/deploy_key.pub` contains an SSH key that you should add
to GitHub as a deploy key for this repository.

The deploy key allows the assignment to update itself automatically
without having to recreate the Docker image.


## Prepare the Gradescope Autograder Zip file

Gradescope requires a zip file to create the Docker image. Before
creating this zip file, make sure `setup.sh` contains the correct
environment for your course.

Then, run the following commands:

```
$ ./build.sh /path/to/a1
```

This will create a file called `autograder-a1-upload.zip`. You can
upload this zip file to Gradescope to create the Docker image.


## Test the Autograder

Given a submission `submission.zip`, you can test the autograder
locally by:

```
$ ./scripts/test_gs_ag.py autograder-a1-upload.zip /path/to/submission.zip
# a new shell is created
$ ./run_autograder
$ exit
```

This will unpack the autograder and submission to a temporary
directory, and run a new shell. If the autograder runs successfully,
on exit it will delete the contents of this temporary directory. You
can always prevent autodeletion by executing `exit 1`.

As you're testing, if you make changes to the source code in
`/path/to/a1`, you can run the `scripts/update.sh` script to update
the autograder _in situ_.

## Running offline tests

TODO
