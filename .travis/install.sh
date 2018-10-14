#!/usr/bin/env bash

pip install setuptools --upgrade

if [ "$TOXENV" != "build" ] ; then
    pip install .[test] --upgrade
fi
