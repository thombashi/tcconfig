#!/bin/bash

commands=(
    "tcset"
    "tcdel"
    "tcshow"
)

for command in "${commands[@]}"; do
    ${command} -h > pages/usage/${command}/${command}_help_output.txt
done
