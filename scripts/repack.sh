#!/bin/bash
# Author: Alex Lee <lee@ccs.neu.edu>
# Repacks all directories ending with .git
# Run periodically on crew-git:/srv/git/repositories

BASE=`pwd`

for x in `ls`; do
    # Bash substring ${var:start-index}
    if [ "${x:(-4)}" == ".git" ]; then
        # Switch into the directory
        cd $BASE
        cd $x
        echo "Repacking: $x"
        # Run repack.
        git repack
    fi
done
