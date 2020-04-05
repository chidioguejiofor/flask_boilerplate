#!/usr/bin/env bash
GIT_DIR=$(   git rev-parse --git-dir )

# Create soft link
echo Creating Soft link

ln -s ../../scripts/pre_commit.sh $GIT_DIR/hooks/pre-commit

echo Soft link created successfully

