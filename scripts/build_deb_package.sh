#!/usr/bin/env bash

set -eux


DIST_DIR_NAME="dist"
INSTALL_DIR_PATH="/usr/bin"
DIST_DIR_PATH="./${DIST_DIR_NAME}/${INSTALL_DIR_PATH}"
PKG_NAME="tcconfig"

# initialize
cd "$(git rev-parse --show-toplevel)"
rm -rf $DIST_DIR_NAME
mkdir -p "${DIST_DIR_NAME}/DEBIAN"

pip install --upgrade "pip>=21.1"
pip install --upgrade .[buildexe,color]

PKG_VERSION=$(python -c "import ${PKG_NAME}; print(${PKG_NAME}.__version__)")

echo "$PKG_NAME $PKG_VERSION"


# build executable binary files
pyinstaller cli_tcset.py --clean --onefile --distpath $DIST_DIR_PATH --name tcset
${DIST_DIR_PATH}/tcset --help

pyinstaller cli_tcdel.py --clean --onefile --distpath $DIST_DIR_PATH --name tcdel
${DIST_DIR_PATH}/tcdel --help

pyinstaller cli_tcshow.py --clean --onefile --distpath $DIST_DIR_PATH --name tcshow
${DIST_DIR_PATH}/tcshow --help


# build a deb package
MACHINE=$(python -c "import platform; print(platform.machine().casefold())")
if [ "$MACHINE" = "x86_64" ]; then
  MACHINE="amd64"
fi

cat << _CONTROL_ > "${DIST_DIR_NAME}/DEBIAN/control"
Package: $PKG_NAME
Version: $PKG_VERSION
Depends: iproute2
Maintainer: Tsuyoshi Hombashi <tsuyoshi.hombashi@gmail.com>
Architecture: $MACHINE
Description: $(cat docs/pages/introduction/summary.txt)
Homepage: https://github.com/thombashi/${PKG_NAME}
Priority: optional
_CONTROL_

VERSION_CODENAME=$(\grep -Po "(?<=VERSION_CODENAME=)[a-z]+" /etc/os-release)

fakeroot dpkg-deb --build "$DIST_DIR_NAME" "$DIST_DIR_NAME"
rename -v "s/_amd64.deb/_${VERSION_CODENAME}_amd64.deb/" ${DIST_DIR_NAME}/*
