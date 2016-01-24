tcconfig

[![Build Status](https://travis-ci.org/thombashi/tcconfig.svg?branch=master)](https://travis-ci.org/thombashi/tcconfig)

# About
Simple tc (traffic control) command wrapper.


# Installation
```console
pip install tcconfig
```


# Usage
## Set traffic control
### tcset help
```console
usage: tcset [-h] [--version] [--logging] [--stacktrace] [--debug | --quiet]
             --device DEVICE [--rate RATE] [--delay DELAY] [--loss LOSS]
             [--overwrite]

optional arguments:
  -h, --help       show this help message and exit
  --version        show program's version number and exit
  --debug          for debug print.
  --quiet          suppress output of execution log message.

Miscellaneous:
  --logging        suppress output of execution log files.
  --stacktrace     display stack trace when an error occurred.

Traffic Control:
  --device DEVICE  network device name
  --rate RATE      network bandwidth [K|M|G bps]
  --delay DELAY    round trip network delay [ms] (default=0)
  --loss LOSS      round trip packet loss rate [%] (default=0)
  --overwrite      overwrite existing setting
```

### e.g. Set a limit on bandwidth up to 100Kbps
```console
# tcset --device eth0 --rate 100k
```

### e.g. Set 100ms network delay
```console
# tcset --device eth0 --delay 100
```

### e.g. Set 0.1% packet loss
```console
# tcset --device eth0 --loss 0.1
```


## Delete traffic control
### tcdel help
```console
usage: tcdel [-h] [--version] [--logging] [--stacktrace] [--debug | --quiet]
             --device DEVICE

optional arguments:
  -h, --help       show this help message and exit
  --version        show program's version number and exit
  --debug          for debug print.
  --quiet          suppress output of execution log message.

Miscellaneous:
  --logging        suppress output of execution log files.
  --stacktrace     display stack trace when an error occurred.

Traffic Control:
  --device DEVICE  network device name
```

### e.g.
```console
# tcdel --device eth0
```
