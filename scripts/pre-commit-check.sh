#!/bin/sh

set -eu

setup_cfg_version() {
    sed -n -e 's/^.*version = \([0-9\.]\+\).*$/\1/p' setup.cfg
}

module_version() {
    sed -n -e 's/^__version__ = "\([0-9\.]\+\)".*$/\1/p' smartbox/__init__.py
}

changelog_version() {
    sed -n -e 's/^.*## \([0-9\.]\+\).*$/\1/p' CHANGELOG.md | head -1
}

if [ "$(setup_cfg_version)" != "$(module_version)" ]
then
    echo "setup.cfg version $(setup_cfg_version) does not match module $(module_version)" >&2
    exit 1
fi

if [ "$(setup_cfg_version)" != "$(changelog_version)" ]
then
    echo "setup.cfg version $(setup_cfg_version) does not match changelog $(changelog_version)" >&2
    exit 1
fi

black --check .
