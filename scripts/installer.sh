#!/usr/bin/env bash

set -eu

if [ $UID -ne 0 ]; then
    echo 'requires superuser privilege' 1>&2
    exit 13
fi

VERSION_CODENAME=$(\grep -Po "(?<=VERSION_CODENAME=)[a-z]+" /etc/os-release)
ARCHIVE_URL=$(curl -sSL https://raw.githubusercontent.com/thombashi/tcconfig/master/info/release_latest.json | jq -r '.assets[].browser_download_url' | \grep -E "tcconfig_.+_${VERSION_CODENAME}_amd64.deb")
TEMP_DIR="$(mktemp -d)"
TEMP_DEB="${TEMP_DIR}/$(basename ${ARCHIVE_URL})"

trap "\rm -rf $TEMP_DIR" 0 1 2 3 15
curl -L "$ARCHIVE_URL" -o "$TEMP_DEB"
dpkg -i "$TEMP_DEB"
