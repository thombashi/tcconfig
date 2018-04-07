#!/usr/bin/env bash

set -u

commands=(
    "tcset"
    "tcdel"
    "tcshow"
)

for command in "${commands[@]}"; do
    output_path=pages/usage/${command}/${command}_help_output.txt
    echo ${output_path}
    ${command} -h > ${output_path}
done
