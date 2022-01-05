#!/bin/sh

set -eu

setup_cfg_version() {
    sed -n -e 's/^.*version = \([0-9\.]\+\).*$/\1/p' setup.cfg
}

changelog_version() {
    sed -n -e 's/^.*## \([0-9\.]\+\).*$/\1/p' CHANGELOG.md | head -1
}

if [ "$(setup_cfg_version)" != "$(changelog_version)" ]
then
    echo "setup.cfg version $(setup_cfg_version) does not match changelog $(changelog_version)" >&2
    exit 1
fi

black --check .

flake8

mypy .
