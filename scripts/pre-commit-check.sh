#!/usr/bin/env zsh

function setup_py_version() {
    sed -n -e 's/^.*version="\([0-9\.]\+\)".*$/\1/p' setup.py
}

function changelog_version() {
    sed -n -e 's/^.*## \([0-9\.]\+\).*$/\1/p' CHANGELOG.md | head -1
}
if [[ $(setup_py_version) != $(changelog_version) ]]
then
    echo "setup.py version $(setup_py_version) does not match changelog $(changelog_version)" >&2
    exit 1
fi
