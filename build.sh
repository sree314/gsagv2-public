#!/bin/bash

P=`dirname $0`

if [ $# -lt 1 ]; then
	echo Usage: $0 path-to-assignment [extra-data-dir]
	exit 1;
fi;

if [ -d "$1" ]; then
	ANAME=`basename "$1"`
	make -C "$P" || exit 1;
	T0=`mktemp -d`
	T=$T0/autograder
	mkdir $T
	unzip $P/autograder.zip -d $T/

	if [ -d "$T/assignment" ]; then
		echo "ERROR: There already exists a directory called 'assignment'"
		exit 1;
	fi;

	cp -a "$1" "$T/"
	mv $T/$ANAME $T/assignment
	realpath "$1" > $T/upstream

	if [ ! -z "$2" ]; then
		if ! cp -a "$2" "$T/" ; then
			echo "ERROR: Could not copy '$2'"
			exit 1;
		fi;
	fi;

	pushd "$T"
	if [ -d "assignment/ssh" ]; then
		cp assignment/ssh/* ssh/
		rm -rf assignment/ssh
	fi;

	zip -r autograder.zip *
	popd

	cp "$T/autograder.zip" ./autograder-$ANAME-upload.zip

	rm -rf "$T0"
else
	echo "ERROR: Directory '$1' does not exist"
	exit 1;
fi;

