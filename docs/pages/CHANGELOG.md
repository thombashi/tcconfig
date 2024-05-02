<a name="v0.28.0"></a>
# [v0.28.0](https://github.com/thombashi/tcconfig/releases/tag/v0.28.0) - 26 Sep 2022

- Fix errors when `tcconfig` commands called with `--quiet` option: [#166](https://github.com/thombashi/tcconfig/issues/166) (Thanks to [@leond08](https://github.com/leond08))
- Add support for `subprocrunner` v2
- Add support for `docker-py` v6
- Change installation path of deb packages from `/usr/bin` to `/usr/local/bin`
- Reduce execution binary size
- Update os of build environments
    - Drop support for Ubuntu 18.04
    - Add support for Ubuntu 22.04
- Avoid using a deprecated module: `pr2modules`

**Full Changelog**: https://github.com/thombashi/tcconfig/compare/v0.27.1...v0.28.0

[Changes][v0.28.0]


<a name="v0.27.1"></a>
# [v0.27.1](https://github.com/thombashi/tcconfig/releases/tag/v0.27.1) - 12 Dec 2021

- Fix `tcconfig` commands failed when installing via binary packages

**Full Changelog**: https://github.com/thombashi/tcconfig/compare/v0.27.0...v0.27.1

[Changes][v0.27.1]


<a name="v0.27.0"></a>
# [v0.27.0](https://github.com/thombashi/tcconfig/releases/tag/v0.27.0) - 12 Dec 2021

- Fix `tcshow` parse error: [#160](https://github.com/thombashi/tcconfig/issues/160) (Thanks to [@personalcomputer](https://github.com/personalcomputer))
- Drop support for Python 3.5
- Add support for Python 3.9/3.10
- Add deb package for each Ubuntu version
- Bump minimum `pyinstaller` version
- Update `tcset` help message
- Remove `setup_requires`
- Replace `path.py` with `path`
- Allow `pyparsing` v3
- Allow `docker-py` v5
- Update requirements

## What's Changed
* Update bug_report.md template to work with new envinfopy syntax by [@personalcomputer](https://github.com/personalcomputer) in https://github.com/thombashi/tcconfig/pull/161

## New Contributors
* [@personalcomputer](https://github.com/personalcomputer) made their first contribution in https://github.com/thombashi/tcconfig/pull/161

**Full Changelog**: https://github.com/thombashi/tcconfig/compare/v0.26.0...v0.27.0

[Changes][v0.27.0]


<a name="v0.26.0"></a>
# [v0.26.0](https://github.com/thombashi/tcconfig/releases/tag/v0.26.0) - 25 Jul 2020

- Add `--tc-command` support with tcset `--import-setting`: [#143](https://github.com/thombashi/tcconfig/issues/143) (Thanks to [@Mnkras](https://github.com/Mnkras))
- Add `--delay-distribution` option to `tcset` command: [#137](https://github.com/thombashi/tcconfig/issues/137) (Thanks to [@severindellsperger](https://github.com/severindellsperger))
- Support importing src-networks: [#144](https://github.com/thombashi/tcconfig/issues/144) (Thanks to [@Mnkras](https://github.com/Mnkras))
- Fix `tcshow` failure when executing `tcshow` at a host that has `tbf` qdiscs
- Don't return a failure if we try to delete a qdisc handle that doesn't exist: [#147](https://github.com/thombashi/tcconfig/issues/147) (Thanks to [@Mnkras](https://github.com/Mnkras))
- Fix `tcconfig` commands to avoid error return code when an ignorable error occurred
- Modify to suppress excessive warning messages of `tcdel` command


[Changes][v0.26.0]


<a name="v0.25.3"></a>
# [v0.25.3](https://github.com/thombashi/tcconfig/releases/tag/v0.25.3) - 19 Jul 2020

- Fix `tcdel` returns non-zero on exit when execute with `--tc-command`/`--tc-script`: [#142](https://github.com/thombashi/tcconfig/issues/142) (Thanks to [@Mnkras](https://github.com/Mnkras))
- Remove execution authority check for `ip` command from `tcdel` when it does not execute `ip` command
- Add wheel package to setup_requires to avoid installation error: [#134](https://github.com/thombashi/tcconfig/issues/134)
- Replace simplejson to ujson and make it to an optional package


[Changes][v0.25.3]


<a name="v0.25.2"></a>
# [v0.25.2](https://github.com/thombashi/tcconfig/releases/tag/v0.25.2) - 01 Mar 2020

- Fix failure when adding filters for both ipv4 and ipv6: [#133](https://github.com/thombashi/tcconfig/issues/133) (Thanks to [@PhilPhonic](https://github.com/PhilPhonic))

[Changes][v0.25.2]


<a name="v0.25.1"></a>
# [v0.25.1](https://github.com/thombashi/tcconfig/releases/tag/v0.25.1) - 16 Feb 2020



[Changes][v0.25.1]


<a name="v0.25.0"></a>
# [v0.25.0](https://github.com/thombashi/tcconfig/releases/tag/v0.25.0) - 16 Feb 2020

- Drop Python 2 support
- Fix logger setup: [#132](https://github.com/thombashi/tcconfig/issues/132)  (Thanks to [@ptone](https://github.com/ptone))
- Add `--dump-db` option to `tcshow` command
- Modify logging formats
- Bug fixes

[Changes][v0.25.0]


<a name="v0.24.1"></a>
# [v0.24.1](https://github.com/thombashi/tcconfig/releases/tag/v0.24.1) - 02 Feb 2020

- Fix `tcconfig` commands failed with `--tc-command`/`--tc-script` option when `iproute2` package not installed: [#130](https://github.com/thombashi/tcconfig/issues/130) (Thanks to [@dkropachev](https://github.com/dkropachev))
- Remove `build`/`buildwhl`/`docs`/`release` `extras_require`
- Replace a dependency from `netifaces` to `pyroute2`


[Changes][v0.24.1]


<a name="v0.24.0"></a>
# [v0.24.0](https://github.com/thombashi/tcconfig/releases/tag/v0.24.0) - 19 Jan 2020

- Add `--exclude-filter-id` option to `tcshow`
- Fix port value conversion to string: [#117](https://github.com/thombashi/tcconfig/issues/117) (Thanks to [@stephenyin](https://github.com/stephenyin))
- Fix error when import tc configs that targeted to Docker containers: [#127](https://github.com/thombashi/tcconfig/issues/127) (Thanks to [@Lawouach](https://github.com/Lawouach))
- Modify `tcshow`  for docker container

[Changes][v0.24.0]


<a name="v0.23.0"></a>
# [v0.23.0](https://github.com/thombashi/tcconfig/releases/tag/v0.23.0) - 12 May 2019

- Add support for Python 3.8
- Drop support for Python 3.4
- Loosen some of the external dependencies version restriction
- Bug fixes

[Changes][v0.23.0]


<a name="v0.22.3"></a>
# [v0.22.3](https://github.com/thombashi/tcconfig/releases/tag/v0.22.3) - 20 Apr 2019



[Changes][v0.22.3]


<a name="v0.22.2"></a>
# [v0.22.2](https://github.com/thombashi/tcconfig/releases/tag/v0.22.2) - 13 Apr 2019

- Fix shaping rule deletion error: [#112](https://github.com/thombashi/tcconfig/issues/112) (Thanks to [@briantsaunders](https://github.com/briantsaunders))
- Fix `tcshow` output


[Changes][v0.22.2]


<a name="v0.22.1"></a>
# [v0.22.1](https://github.com/thombashi/tcconfig/releases/tag/v0.22.1) - 18 Mar 2019

- Fix configuration importing failed at Python 2 environments: [#110](https://github.com/thombashi/tcconfig/issues/110) (Thanks to [@XN137](https://github.com/XN137))
- Fix `--overwrite` option not properly worked when configuration imports
- Improve checks for bandwidth rate upper limit
- Bug fixes


[Changes][v0.22.1]


<a name="v0.22.0"></a>
# [v0.22.0](https://github.com/thombashi/tcconfig/releases/tag/v0.22.0) - 17 Mar 2019

- Improve human-readable value support for `tcset` options
- Add support for `direct_qlen` to `tcshow`


[Changes][v0.22.0]


<a name="v0.21.9"></a>
# [v0.21.9](https://github.com/thombashi/tcconfig/releases/tag/v0.21.9) - 26 Feb 2019

- Avoid an error when there are no `qdiscs` to delete by `tcdel` on fedora environments: [#108](https://github.com/thombashi/tcconfig/issues/108) (Thanks to [@rukmarr](https://github.com/rukmarr))
- Fix `iptables` bin path extraction for fedora environments

[Changes][v0.21.9]


<a name="v0.21.8"></a>
# [v0.21.8](https://github.com/thombashi/tcconfig/releases/tag/v0.21.8) - 10 Feb 2019

- Improve the minimum bandwidth rate validation: [#106](https://github.com/thombashi/tcconfig/issues/106) (Thanks to [@sanhar](https://github.com/sanhar))
- Improve log messages
- Improve deb packaging


[Changes][v0.21.8]


<a name="v0.21.7"></a>
# [v0.21.7](https://github.com/thombashi/tcconfig/releases/tag/v0.21.7) - 03 Feb 2019

- Bug fix: avoid `tcconfing` commands execution fails that environment where Docker not installed
- Bug fix: avoid `tcconfing` commands execution fails when failed to create `veth` mapping
- Pin `pip` version to lower than 19 to avoid packaging failure:  pypa/pip#6163


[Changes][v0.21.7]


<a name="v0.21.6"></a>
# [v0.21.6](https://github.com/thombashi/tcconfig/releases/tag/v0.21.6) - 22 Jan 2019

- Avoid an error caused by version mismatch of docker client and server: [#103](https://github.com/thombashi/tcconfig/issues/103) (Thanks to [@tazhate](https://github.com/tazhate) / [@Wolfeg](https://github.com/Wolfeg))
- Add `--debug-query` option


[Changes][v0.21.6]


<a name="v0.21.5"></a>
# [v0.21.5](https://github.com/thombashi/tcconfig/releases/tag/v0.21.5) - 20 Jan 2019



[Changes][v0.21.5]


<a name="v0.21.4"></a>
# [v0.21.4](https://github.com/thombashi/tcconfig/releases/tag/v0.21.4) - 13 Jan 2019



[Changes][v0.21.4]


<a name="v0.21.3"></a>
# [v0.21.3](https://github.com/thombashi/tcconfig/releases/tag/v0.21.3) - 03 Jan 2019



[Changes][v0.21.3]


<a name="v0.21.2"></a>
# [v0.21.2](https://github.com/thombashi/tcconfig/releases/tag/v0.21.2) - 30 Dec 2018

- Change to accept `%` unit for netem parameters
- Fix `tcset` command that `--change` option not properly reflected the output when using `--tc-command`/`--tc-script` options

[Changes][v0.21.2]


<a name="v0.21.1"></a>
# [v0.21.1](https://github.com/thombashi/tcconfig/releases/tag/v0.21.1) - 24 Dec 2018



[Changes][v0.21.1]


<a name="v0.21.0"></a>
# [v0.21.0](https://github.com/thombashi/tcconfig/releases/tag/v0.21.0) - 14 Oct 2018

- Add `--dst-container`/`--dst-container` options to `tcset`/`tcdel`
- Loosen external package dependencies
- Bug fixes

[Changes][v0.21.0]


<a name="v0.20.3"></a>
# [v0.20.3](https://github.com/thombashi/tcconfig/releases/tag/v0.20.3) - 30 Sep 2018

- Fix package meta data

[Changes][v0.20.3]


<a name="v0.20.2"></a>
# [v0.20.2](https://github.com/thombashi/tcconfig/releases/tag/v0.20.2) - 09 Sep 2018



[Changes][v0.20.2]


<a name="v0.20.1"></a>
# [v0.20.1](https://github.com/thombashi/tcconfig/releases/tag/v0.20.1) - 19 Aug 2018

- Fix error handling for reordering parameter: [#101](https://github.com/thombashi/tcconfig/issues/101) (Thanks to [@ColinMcMicken](https://github.com/ColinMcMicken))

[Changes][v0.20.1]


<a name="v0.20.0"></a>
# [v0.20.0](https://github.com/thombashi/tcconfig/releases/tag/v0.20.0) - 05 Aug 2018

- Add support for Docker
- Reduce hash conflict when generating tc scripts: [#100](https://github.com/thombashi/tcconfig/issues/100) (Thanks to [@user-name-is-taken](https://github.com/user-name-is-taken))
- Bug fixes

[Changes][v0.20.0]


<a name="v0.19.1"></a>
# [v0.19.1](https://github.com/thombashi/tcconfig/releases/tag/v0.19.1) - 27 Jul 2018

- Fix `tcset` command execution failed when all of the following conditions:
    - Using `--tc-command` option with `--direction incoming` option
    - `netifaces` package is installed.


[Changes][v0.19.1]


<a name="v0.19.0"></a>
# [v0.19.0](https://github.com/thombashi/tcconfig/releases/tag/v0.19.0) - 16 Jul 2018

- Change `-d`/`--device` option of tcconfig commands into a positional argument
    - e.g. `tcset eth0 --rate 1Mbps`
    - `-d`/`--device` option still can be used for backward compatibility
- Change `tcset` `-f` option to `--import-setting` option
- Add `--color` option to `tcshow` command
- Add support for Python 3.7
- Introduce colorized logging
- Fix choices for `--shaping-algo` option
- Bug fixes


[Changes][v0.19.0]


<a name="v0.18.3"></a>
# [v0.18.3](https://github.com/thombashi/tcconfig/releases/tag/v0.18.3) - 02 Jul 2018



[Changes][v0.18.3]


<a name="v0.18.2"></a>
# [v0.18.2](https://github.com/thombashi/tcconfig/releases/tag/v0.18.2) - 04 May 2018

- Add support for Linux capability of the `--direction incoming` option
- Fix `tcconfig` commands failed when missing optional packages
- Improve log messages
- Bug fixes

[Changes][v0.18.2]


<a name="v0.18.1"></a>
# [v0.18.1](https://github.com/thombashi/tcconfig/releases/tag/v0.18.1) - 22 Apr 2018



[Changes][v0.18.1]


<a name="v0.18.0"></a>
# [v0.18.0](https://github.com/thombashi/tcconfig/releases/tag/v0.18.0) - 08 Apr 2018

- Add support for Linux capabilities: [#98](https://github.com/thombashi/tcconfig/issues/98) (Thanks to [@dastergon](https://github.com/dastergon) )
- Bug fixes

[Changes][v0.18.0]


<a name="v0.17.3"></a>
# [v0.17.3](https://github.com/thombashi/tcconfig/releases/tag/v0.17.3) - 04 Feb 2018

- Add execution permission check to `tcset`/`tcdel`
- Suppress excessive log message output


[Changes][v0.17.3]


<a name="v0.17.2"></a>
# [v0.17.2](https://github.com/thombashi/tcconfig/releases/tag/v0.17.2) - 20 Jan 2018

- Fix tcdel for the deb package: [#93](https://github.com/thombashi/tcconfig/issues/93) (Thanks to [@pxsalehi](https://github.com/pxsalehi))
- Bugfix for `tcshow`

[Changes][v0.17.2]


<a name="v0.17.1"></a>
# [v0.17.1](https://github.com/thombashi/tcconfig/releases/tag/v0.17.1) - 29 Dec 2017

- Add a deb package

[Changes][v0.17.1]


<a name="v0.17.0"></a>
# [v0.17.0](https://github.com/thombashi/tcconfig/releases/tag/v0.17.0) - 04 Nov 2017

- Improve log messages
- Drop support for Python 3.3


[Changes][v0.17.0]


<a name="v0.16.2"></a>
# [v0.16.2](https://github.com/thombashi/tcconfig/releases/tag/v0.16.2) - 28 Oct 2017

- Fix improper `tcdel` output when executed with `--tc-command`/`--tc-script` options
- Suppress an excessive warning message that outputted when executed with `--tc-command`/`--tc-script` options


[Changes][v0.16.2]


<a name="v0.16.1"></a>
# [v0.16.1](https://github.com/thombashi/tcconfig/releases/tag/v0.16.1) - 17 Oct 2017



[Changes][v0.16.1]


<a name="v0.16.0"></a>
# [v0.16.0](https://github.com/thombashi/tcconfig/releases/tag/v0.16.0) - 08 Oct 2017

- Change `--change` option behavior to add a shaping rule if there are no existing rules: [#88](https://github.com/thombashi/tcconfig/issues/88) (Thanks to [@dastergon](https://github.com/dastergon))
- Improve error messages
- Bug fixes

[Changes][v0.16.0]


<a name="v0.15.0"></a>
# [v0.15.0](https://github.com/thombashi/tcconfig/releases/tag/v0.15.0) - 02 Sep 2017

- Support extra time units in delay specification: [#86](https://github.com/thombashi/tcconfig/issues/86) (Thanks to [@dastergon](https://github.com/dastergon))
- Improve log messages


[Changes][v0.15.0]


<a name="v0.14.1"></a>
# [v0.14.1](https://github.com/thombashi/tcconfig/releases/tag/v0.14.1) - 19 Aug 2017

- Fix qdisc handle parsing failed when the handle include alphabet: [#85](https://github.com/thombashi/tcconfig/issues/85) (Thanks to [@selimt](https://github.com/selimt))
- Fix tcdel failed when deleting the final filter with Python 3


[Changes][v0.14.1]


<a name="v0.14.0"></a>
# [v0.14.0](https://github.com/thombashi/tcconfig/releases/tag/v0.14.0) - 18 Aug 2017

- Add support for deletion per-network to `tcdel`: [#80](https://github.com/thombashi/tcconfig/issues/80) (Thanks to [@dastergon](https://github.com/dastergon))
- Suppress unnecessary log messages when add/change shaping rules: [#84](https://github.com/thombashi/tcconfig/issues/84) (Thanks to [@dastergon](https://github.com/dastergon))
- Bug fixes

[Changes][v0.14.0]


<a name="v0.13.2"></a>
# [v0.13.2](https://github.com/thombashi/tcconfig/releases/tag/v0.13.2) - 16 Aug 2017

- Fix `tcset --change` option alters other defined rules: [#79](https://github.com/thombashi/tcconfig/issues/79) (Thanks to [@dastergon](https://github.com/dastergon))
- Add config file existence check for the `tcset`
- Add `--stacktrace` option for debugging
- Improve log messages
- Bug fixes

[Changes][v0.13.2]


<a name="v0.13.1"></a>
# [v0.13.1](https://github.com/thombashi/tcconfig/releases/tag/v0.13.1) - 08 Aug 2017

- Fix handles negative NIC speed values: [#81](https://github.com/thombashi/tcconfig/issues/81) (Thanks to [@dastergon](https://github.com/dastergon))

[Changes][v0.13.1]


<a name="v0.13.0"></a>
# [v0.13.0](https://github.com/thombashi/tcconfig/releases/tag/v0.13.0) - 06 Aug 2017

- Add exclude options: [#77](https://github.com/thombashi/tcconfig/issues/77) (Thanks to [@dastergon](https://github.com/dastergon))
    - `--exclude-dst-network`
    - `--exclude-src-network`
    - `--exclude-dst-port`
    - `--exclude-src-port`
- Modify to `--src-network` option can be used without the `--iptables` option when using `htb`
- Bug fixes


[Changes][v0.13.0]


<a name="v0.12.2"></a>
# [v0.12.2](https://github.com/thombashi/tcconfig/releases/tag/v0.12.2) - 03 Aug 2017

- Add a short option for the ``--device`` option
- Fix ``tcset`` failed when using ``tbf``


[Changes][v0.12.2]


<a name="v0.12.1"></a>
# [v0.12.1](https://github.com/thombashi/tcconfig/releases/tag/v0.12.1) - 17 Jul 2017



[Changes][v0.12.1]


<a name="v0.12.0"></a>
# [v0.12.0](https://github.com/thombashi/tcconfig/releases/tag/v0.12.0) - 11 Jun 2017

- Add `--change option` to reduce shaping rule changing side effect: [#68](https://github.com/thombashi/tcconfig/issues/68) (Thanks to [@twdkeule](https://github.com/twdkeule))
- Make a script file name created by `tcshow --tc-script` include target device names.
- Improve log messages
- Bug fix
    - Avoid adding a shaping rule where a rule already existing path: [#70](https://github.com/thombashi/tcconfig/issues/70) (Thanks to [@twdkeule](https://github.com/twdkeule))
    - Modify to return proper exit code: [#71](https://github.com/thombashi/tcconfig/issues/71) (Thanks to [@twdkeule](https://github.com/twdkeule))
    - Fix packaging
    - Minor bug fixes


[Changes][v0.12.0]


<a name="v0.11.0"></a>
# [v0.11.0](https://github.com/thombashi/tcconfig/releases/tag/v0.11.0) - 06 Jun 2017

- Add `--duplicate`/`--reordering` options: [#67](https://github.com/thombashi/tcconfig/issues/67) (Thanks to [@Sir-Nightmare](https://github.com/Sir-Nightmare))
- Make `tcset`/`tcdel` commands executable without `tc` command installed when `--tc-command`/`--tc-script` options are used.


[Changes][v0.11.0]


<a name="v0.10.0"></a>
# [v0.10.0](https://github.com/thombashi/tcconfig/releases/tag/v0.10.0) - 06 May 2017

- Add `--src-port` option: [#51](https://github.com/thombashi/tcconfig/issues/51) (Thanks to [@lauhen](https://github.com/lauhen))
- Bug fixes
- Improve log messages

[Changes][v0.10.0]


<a name="v0.9.0"></a>
# [v0.9.0](https://github.com/thombashi/tcconfig/releases/tag/v0.9.0) - 25 Mar 2017

- Add IPv6 support (Thanks to [@rkd-msw](https://github.com/rkd-msw)): [#61](https://github.com/thombashi/tcconfig/issues/61) [#62](https://github.com/thombashi/tcconfig/issues/62) 
- Bug fixes


[Changes][v0.9.0]


<a name="v0.8.0"></a>
# [v0.8.0](https://github.com/thombashi/tcconfig/releases/tag/v0.8.0) - 18 Mar 2017

[#59](https://github.com/thombashi/tcconfig/issues/59): Thanks to [@pedro-nonfree](https://github.com/pedro-nonfree)

- Add ``--tc-command`` option: display tc commands to be executed by tcconfig commands
- Add ``--tc-script`` option: create a tc command script which include commands to be executed by tcconfig 


[Changes][v0.8.0]


<a name="v0.7.2"></a>
# [v0.7.2](https://github.com/thombashi/tcconfig/releases/tag/v0.7.2) - 11 Mar 2017

- Fix error handling ([#57](https://github.com/thombashi/tcconfig/issues/57): Thanks to [@eroullit](https://github.com/eroullit))


[Changes][v0.7.2]


<a name="v0.7.1"></a>
# [v0.7.1](https://github.com/thombashi/tcconfig/releases/tag/v0.7.1) - 25 Feb 2017

- Fix [#54](https://github.com/thombashi/tcconfig/issues/54) failed to execute tcset when iproute2 version is older than 3.14.0 (Thanks to [@ducalpha](https://github.com/ducalpha))
- Bug fixes


[Changes][v0.7.1]


<a name="0.7.1-alpha"></a>
# [0.7.1-alpha](https://github.com/thombashi/tcconfig/releases/tag/0.7.1-alpha) - 15 Feb 2017



[Changes][0.7.1-alpha]


<a name="v0.7.0"></a>
# [v0.7.0](https://github.com/thombashi/tcconfig/releases/tag/v0.7.0) - 22 Jan 2017

- [#30](https://github.com/thombashi/tcconfig/issues/30): Filter routes support. Thanks to [@JonathanLennox](https://github.com/JonathanLennox)
- [#39](https://github.com/thombashi/tcconfig/issues/39): Allow 100% packet loss/corruption settings. Thanks to [@pdavies](https://github.com/pdavies).
- [#43](https://github.com/thombashi/tcconfig/issues/43): Multiple rules support. Thanks to [@konetzed](https://github.com/konetzed) 
  - Add `--add` option
- Change default shaping algorithm from tbf to htb
- Python 3.6 support
- Improve log messages
- Bug fixes


[Changes][v0.7.0]


<a name="v0.7.0-alpha-4"></a>
# [v0.7.0-alpha-4](https://github.com/thombashi/tcconfig/releases/tag/v0.7.0-alpha-4) - 17 Jan 2017

- Bugfix: shaping rules not applied properly when using htb algorithm and not using network/port options


[Changes][v0.7.0-alpha-4]


<a name="v0.7.0-alpha-3"></a>
# [v0.7.0-alpha-3](https://github.com/thombashi/tcconfig/releases/tag/v0.7.0-alpha-3) - 15 Jan 2017

- Multiple rules support [#43](https://github.com/thombashi/tcconfig/issues/43): Thanks to [@konetzed](https://github.com/konetzed) 
  - Add `--add` option
  - Add `--shaping-algo` option
- Bug fixes
- Improve log messages
- Limitation:
  - Currently `tcshow` will not properly worked when using `htb` as `--shaping-algo`.
- Python 3.6 support


[Changes][v0.7.0-alpha-3]


<a name="v0.7.0-alpha-2"></a>
# [v0.7.0-alpha-2](https://github.com/thombashi/tcconfig/releases/tag/v0.7.0-alpha-2) - 07 Jan 2017

- [#39](https://github.com/thombashi/tcconfig/issues/39): Allow 100% packet loss/corruption settings. Thanks to [@pdavies](https://github.com/pdavies).


[Changes][v0.7.0-alpha-2]


<a name="v0.7.0-alpha"></a>
# [v0.7.0-alpha](https://github.com/thombashi/tcconfig/releases/tag/v0.7.0-alpha) - 06 Nov 2016

- [#30](https://github.com/thombashi/tcconfig/issues/30) 
- Bug fixes


[Changes][v0.7.0-alpha]


<a name="v0.6.6"></a>
# [v0.6.6](https://github.com/thombashi/tcconfig/releases/tag/v0.6.6) - 28 Aug 2016

- Fix config file loading of tcset command


[Changes][v0.6.6]


<a name="v0.6.5"></a>
# [v0.6.5](https://github.com/thombashi/tcconfig/releases/tag/v0.6.5) - 26 Aug 2016

- Suppress excessive error messages


[Changes][v0.6.5]


<a name="v0.6.4"></a>
# [v0.6.4](https://github.com/thombashi/tcconfig/releases/tag/v0.6.4) - 13 Aug 2016

- Fix package dependency


[Changes][v0.6.4]


<a name="v0.6.3"></a>
# [v0.6.3](https://github.com/thombashi/tcconfig/releases/tag/v0.6.3) - 13 Aug 2016

- Drop support for Python 2.6
- Modify package dependency
- Bug fixes
- Refactoring


[Changes][v0.6.3]


<a name="v0.6.2"></a>
# [v0.6.2](https://github.com/thombashi/tcconfig/releases/tag/v0.6.2) - 19 Jun 2016

- Make pytest-runner a conditional requirement
- Drop support for Python 2.5


[Changes][v0.6.2]


<a name="v0.6.1"></a>
# [v0.6.1](https://github.com/thombashi/tcconfig/releases/tag/v0.6.1) - 19 Mar 2016

- Fix requirements
- Improve python3 compatibility


[Changes][v0.6.1]


<a name="v0.6.0"></a>
# [v0.6.0](https://github.com/thombashi/tcconfig/releases/tag/v0.6.0) - 13 Mar 2016

# Enhancement
- Add a command line option to set traffic control from configuration file
- Change to be able to set the floating point with network latency

# Fix
- Fix tcset: failed to incoming filtering for multiple network interfaces


[Changes][v0.6.0]


<a name="v0.5.0"></a>
# [v0.5.0](https://github.com/thombashi/tcconfig/releases/tag/v0.5.0) - 12 Mar 2016

# Enhancement
- Add tcshow command to display tc configurations as more human-readable format

# Fix
- Fix filtering with port-number


[Changes][v0.5.0]


<a name="v0.4.0"></a>
# [v0.4.0](https://github.com/thombashi/tcconfig/releases/tag/v0.4.0) - 06 Mar 2016

# Enhancement
- Add packet corruption rate support
- Add network latency distribution support


[Changes][v0.4.0]


<a name="v0.3.0"></a>
# [v0.3.0](https://github.com/thombashi/tcconfig/releases/tag/v0.3.0) - 05 Mar 2016

# Enhancement

Add support for incoming packet traffic control


[Changes][v0.3.0]


<a name="v0.2.0"></a>
# [v0.2.0](https://github.com/thombashi/tcconfig/releases/tag/v0.2.0) - 03 Mar 2016

# Enhancement
- Add network/port options


[Changes][v0.2.0]


<a name="v0.1.4"></a>
# [v0.1.4](https://github.com/thombashi/tcconfig/releases/tag/v0.1.4) - 01 Mar 2016



[Changes][v0.1.4]


<a name="v0.1.3"></a>
# [v0.1.3](https://github.com/thombashi/tcconfig/releases/tag/v0.1.3) - 22 Feb 2016



[Changes][v0.1.3]


<a name="v0.1.2"></a>
# [v0.1.2](https://github.com/thombashi/tcconfig/releases/tag/v0.1.2) - 31 Jan 2016



[Changes][v0.1.2]


<a name="v0.1.1"></a>
# [v0.1.1](https://github.com/thombashi/tcconfig/releases/tag/v0.1.1) - 23 Jan 2016



[Changes][v0.1.1]


<a name="v0.1.0"></a>
# [v0.1.0](https://github.com/thombashi/tcconfig/releases/tag/v0.1.0) - 18 Jan 2016



[Changes][v0.1.0]


[v0.28.0]: https://github.com/thombashi/tcconfig/compare/v0.27.1...v0.28.0
[v0.27.1]: https://github.com/thombashi/tcconfig/compare/v0.27.0...v0.27.1
[v0.27.0]: https://github.com/thombashi/tcconfig/compare/v0.26.0...v0.27.0
[v0.26.0]: https://github.com/thombashi/tcconfig/compare/v0.25.3...v0.26.0
[v0.25.3]: https://github.com/thombashi/tcconfig/compare/v0.25.2...v0.25.3
[v0.25.2]: https://github.com/thombashi/tcconfig/compare/v0.25.1...v0.25.2
[v0.25.1]: https://github.com/thombashi/tcconfig/compare/v0.25.0...v0.25.1
[v0.25.0]: https://github.com/thombashi/tcconfig/compare/v0.24.1...v0.25.0
[v0.24.1]: https://github.com/thombashi/tcconfig/compare/v0.24.0...v0.24.1
[v0.24.0]: https://github.com/thombashi/tcconfig/compare/v0.23.0...v0.24.0
[v0.23.0]: https://github.com/thombashi/tcconfig/compare/v0.22.3...v0.23.0
[v0.22.3]: https://github.com/thombashi/tcconfig/compare/v0.22.2...v0.22.3
[v0.22.2]: https://github.com/thombashi/tcconfig/compare/v0.22.1...v0.22.2
[v0.22.1]: https://github.com/thombashi/tcconfig/compare/v0.22.0...v0.22.1
[v0.22.0]: https://github.com/thombashi/tcconfig/compare/v0.21.9...v0.22.0
[v0.21.9]: https://github.com/thombashi/tcconfig/compare/v0.21.8...v0.21.9
[v0.21.8]: https://github.com/thombashi/tcconfig/compare/v0.21.7...v0.21.8
[v0.21.7]: https://github.com/thombashi/tcconfig/compare/v0.21.6...v0.21.7
[v0.21.6]: https://github.com/thombashi/tcconfig/compare/v0.21.5...v0.21.6
[v0.21.5]: https://github.com/thombashi/tcconfig/compare/v0.21.4...v0.21.5
[v0.21.4]: https://github.com/thombashi/tcconfig/compare/v0.21.3...v0.21.4
[v0.21.3]: https://github.com/thombashi/tcconfig/compare/v0.21.2...v0.21.3
[v0.21.2]: https://github.com/thombashi/tcconfig/compare/v0.21.1...v0.21.2
[v0.21.1]: https://github.com/thombashi/tcconfig/compare/v0.21.0...v0.21.1
[v0.21.0]: https://github.com/thombashi/tcconfig/compare/v0.20.3...v0.21.0
[v0.20.3]: https://github.com/thombashi/tcconfig/compare/v0.20.2...v0.20.3
[v0.20.2]: https://github.com/thombashi/tcconfig/compare/v0.20.1...v0.20.2
[v0.20.1]: https://github.com/thombashi/tcconfig/compare/v0.20.0...v0.20.1
[v0.20.0]: https://github.com/thombashi/tcconfig/compare/v0.19.1...v0.20.0
[v0.19.1]: https://github.com/thombashi/tcconfig/compare/v0.19.0...v0.19.1
[v0.19.0]: https://github.com/thombashi/tcconfig/compare/v0.18.3...v0.19.0
[v0.18.3]: https://github.com/thombashi/tcconfig/compare/v0.18.2...v0.18.3
[v0.18.2]: https://github.com/thombashi/tcconfig/compare/v0.18.1...v0.18.2
[v0.18.1]: https://github.com/thombashi/tcconfig/compare/v0.18.0...v0.18.1
[v0.18.0]: https://github.com/thombashi/tcconfig/compare/v0.17.3...v0.18.0
[v0.17.3]: https://github.com/thombashi/tcconfig/compare/v0.17.2...v0.17.3
[v0.17.2]: https://github.com/thombashi/tcconfig/compare/v0.17.1...v0.17.2
[v0.17.1]: https://github.com/thombashi/tcconfig/compare/v0.17.0...v0.17.1
[v0.17.0]: https://github.com/thombashi/tcconfig/compare/v0.16.2...v0.17.0
[v0.16.2]: https://github.com/thombashi/tcconfig/compare/v0.16.1...v0.16.2
[v0.16.1]: https://github.com/thombashi/tcconfig/compare/v0.16.0...v0.16.1
[v0.16.0]: https://github.com/thombashi/tcconfig/compare/v0.15.0...v0.16.0
[v0.15.0]: https://github.com/thombashi/tcconfig/compare/v0.14.1...v0.15.0
[v0.14.1]: https://github.com/thombashi/tcconfig/compare/v0.14.0...v0.14.1
[v0.14.0]: https://github.com/thombashi/tcconfig/compare/v0.13.2...v0.14.0
[v0.13.2]: https://github.com/thombashi/tcconfig/compare/v0.13.1...v0.13.2
[v0.13.1]: https://github.com/thombashi/tcconfig/compare/v0.13.0...v0.13.1
[v0.13.0]: https://github.com/thombashi/tcconfig/compare/v0.12.2...v0.13.0
[v0.12.2]: https://github.com/thombashi/tcconfig/compare/v0.12.1...v0.12.2
[v0.12.1]: https://github.com/thombashi/tcconfig/compare/v0.12.0...v0.12.1
[v0.12.0]: https://github.com/thombashi/tcconfig/compare/v0.11.0...v0.12.0
[v0.11.0]: https://github.com/thombashi/tcconfig/compare/v0.10.0...v0.11.0
[v0.10.0]: https://github.com/thombashi/tcconfig/compare/v0.9.0...v0.10.0
[v0.9.0]: https://github.com/thombashi/tcconfig/compare/v0.8.0...v0.9.0
[v0.8.0]: https://github.com/thombashi/tcconfig/compare/v0.7.2...v0.8.0
[v0.7.2]: https://github.com/thombashi/tcconfig/compare/v0.7.1...v0.7.2
[v0.7.1]: https://github.com/thombashi/tcconfig/compare/0.7.1-alpha...v0.7.1
[0.7.1-alpha]: https://github.com/thombashi/tcconfig/compare/v0.7.0...0.7.1-alpha
[v0.7.0]: https://github.com/thombashi/tcconfig/compare/v0.7.0-alpha-4...v0.7.0
[v0.7.0-alpha-4]: https://github.com/thombashi/tcconfig/compare/v0.7.0-alpha-3...v0.7.0-alpha-4
[v0.7.0-alpha-3]: https://github.com/thombashi/tcconfig/compare/v0.7.0-alpha-2...v0.7.0-alpha-3
[v0.7.0-alpha-2]: https://github.com/thombashi/tcconfig/compare/v0.7.0-alpha...v0.7.0-alpha-2
[v0.7.0-alpha]: https://github.com/thombashi/tcconfig/compare/v0.6.6...v0.7.0-alpha
[v0.6.6]: https://github.com/thombashi/tcconfig/compare/v0.6.5...v0.6.6
[v0.6.5]: https://github.com/thombashi/tcconfig/compare/v0.6.4...v0.6.5
[v0.6.4]: https://github.com/thombashi/tcconfig/compare/v0.6.3...v0.6.4
[v0.6.3]: https://github.com/thombashi/tcconfig/compare/v0.6.2...v0.6.3
[v0.6.2]: https://github.com/thombashi/tcconfig/compare/v0.6.1...v0.6.2
[v0.6.1]: https://github.com/thombashi/tcconfig/compare/v0.6.0...v0.6.1
[v0.6.0]: https://github.com/thombashi/tcconfig/compare/v0.5.0...v0.6.0
[v0.5.0]: https://github.com/thombashi/tcconfig/compare/v0.4.0...v0.5.0
[v0.4.0]: https://github.com/thombashi/tcconfig/compare/v0.3.0...v0.4.0
[v0.3.0]: https://github.com/thombashi/tcconfig/compare/v0.2.0...v0.3.0
[v0.2.0]: https://github.com/thombashi/tcconfig/compare/v0.1.4...v0.2.0
[v0.1.4]: https://github.com/thombashi/tcconfig/compare/v0.1.3...v0.1.4
[v0.1.3]: https://github.com/thombashi/tcconfig/compare/v0.1.2...v0.1.3
[v0.1.2]: https://github.com/thombashi/tcconfig/compare/v0.1.1...v0.1.2
[v0.1.1]: https://github.com/thombashi/tcconfig/compare/v0.1.0...v0.1.1
[v0.1.0]: https://github.com/thombashi/tcconfig/tree/v0.1.0

<!-- Generated by https://github.com/rhysd/changelog-from-release v3.7.2 -->
