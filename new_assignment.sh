#!/bin/bash

P=`dirname $0`
if [ $# -lt 1 ]; then
	echo "Usage: $0 /path/to/newassignment"
	echo "newassignment should be the directory inside submitted zip file, e.g. 'a1'"
	exit 1;
fi;

DST="$1"
ASSIGNMENT=`basename "$DST"`

if mkdir -p "$DST"; then
	cp -va $P/assignment_template/* "$DST" && mv "$DST/gitignore" "$DST/.gitignore"
	cp -va $P/checkerutils/checkerutils "$DST"

	sed -i "s/ZIP_ROOT = 'aX'.*/ZIP_ROOT = '$ASSIGNMENT'/" "$DST/checker.py"

	if [ ! -f "$DST/ssh/deploy_key" ]; then
		mkdir -p "$DST/ssh" &&  ssh-keygen -N "" -f "$DST/ssh/deploy_key"
	fi;

	pushd "$DST"; git init && git add . &&  git commit -am 'Initial commit'; popd
fi;
