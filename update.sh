#!/bin/bash
P=`dirname $0`
if [ -f "$P/upstream" ]; then
	rsync --exclude 'ssh' -av `cat $P/upstream`/ $P/assignment/
fi;
