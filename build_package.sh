#!/usr/bin/env bash

if [ "$TRAVIS_OS_NAME" = "linux" ] && [ "$TOXENV" = "build" ] ; then
    sudo apt -qq update
    sudo apt install -y fakeroot
    bash -x build_deb_package.sh
fi
