#!/bin/bash

set -eu

dist_dir="tcconfig_wheel"
wheelhouse_dir_path=${dist_dir}/"wheelhouse"
install_script_path=${dist_dir}/"install.sh"
lancher_script="launcher.sh"


pip install pip --upgrade

# make wheelhouse ---
python setup.py bdist_wheel --dist-dir ${dist_dir} --universal
pip wheel -r requirements/requirements.txt --wheel-dir ${wheelhouse_dir_path}

rm ${wheelhouse_dir_path}/Logbook-*.whl
pip download Logbook --no-deps --dest ${wheelhouse_dir_path}


# make an install script ---
cat <<EOF > ${install_script_path}
#!/bin/sh

set -eu

pip install --use-wheel --no-index --find-links=wheelhouse tcconfig-*.whl --upgrade
EOF

chmod +x ${install_script_path}


# make an archive file ---
tar cvf tcconfig_wheel.tar.gz tcconfig_wheel
