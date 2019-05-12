#!/usr/bin/env bash

pip install setuptools --upgrade

if [ "$TOXENV" != "build" ] ; then
    pip install tox --upgrade
fi
