#!/bin/bash

BASE_DIR=$(git rev-parse --show-toplevel)
HOOK_DIR=$BASE_DIR/.git/hooks

if [ -x $0.local ]; then
    $0.local "$@" || exit $?
fi
if [ -x $BASE_DIR/scripts/git-hooks/$(basename $0) ]; then
    $BASE_DIR/scripts/git-hooks/$(basename $0) "$@" || exit $?
fi