#!/bin/sh

set -eu

setup_cfg_version() {
    sed -n -e 's/^.*version = \([0-9\.]\+\(-[a-z0-9\.]\+\)\?\).*$/\1/p' setup.cfg
}

module_version() {
    sed -n -e 's/^__version__ = "\([0-9\.]\+\(-[a-z0-9\.]\+\)\?\)".*$/\1/p' smartbox/__init__.py
}

echo Checking module and setup.cfg versions match...
if [ "$(setup_cfg_version)" != "$(module_version)" ]
then
    echo "setup.cfg version $(setup_cfg_version) does not match module $(module_version)" >&2
    exit 1
fi

echo Checking black formatting...
black --check .

echo Checking flake8...
flake8

echo Checking mypy...
mypy .
