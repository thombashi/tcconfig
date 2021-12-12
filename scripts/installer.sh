#!/usr/bin/env bash

set -eu

if [ $UID -ne 0 ]; then
    echo 'requires superuser privilege' 1>&2
    exit 13
fi

ARCHIVE_URL=$(curl -sSL https://raw.githubusercontent.com/thombashi/tcconfig/master/info/release_latest.json | jq -r '.assets[].browser_download_url' | \grep deb)
TEMP_DEB="$(mktemp)"

trap "\rm -f $TEMP_DEB" 0 1 2 3 15
curl -L "$ARCHIVE_URL" -o "$TEMP_DEB"
dpkg -i "$TEMP_DEB"
