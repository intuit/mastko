#!/bin/bash

HOOK_NAMES="pre-commit pre-merge-commit prepare-commit-msg commit-msg post-commit pre-rebase post-checkout post-merge pre-push"

HOOK_DIR=$(git rev-parse --show-toplevel)/.git/hooks

for hook in $HOOK_NAMES; do
    if [ ! -h $HOOK_DIR/$hook -a -x $HOOK_DIR/$hook ]; then
        mv $HOOK_DIR/$hook $HOOK_DIR/$hook.local
    fi
    ln -s -f $(git rev-parse --show-toplevel)/scripts/git-hooks/hooks-wrapper.sh $HOOK_DIR/$hook
done