from __future__ import with_statement
import sys
import setuptools

import tcconfig


with open("README.rst") as fp:
    long_description = fp.read()

with open("requirements.txt", "r") as fp:
    requirements = fp.read().splitlines()

major, minor = sys.version_info[:2]
if major == 2 and minor <= 5:
    requirements.extend([
        "argparse",
    ])

setuptools.setup(
    name="tcconfig",
    version=tcconfig.VERSION,
    author="Tsuyoshi Hombashi",
    author_email="gogogo.vm@gmail.com",
    url="https://github.com/thombashi/tcconfig",
    description="Simple tc (traffic control) command wrapper",
    long_description=long_description,
    license="MIT License",
    include_package_data=True,
    packages=setuptools.find_packages(exclude=['test*']),
    install_requires=requirements,
    setup_requires=["pytest-runner"],
    tests_require=["pytest"],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.5",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.3",
        "Programming Language :: Python :: 3.4",
        "Topic :: System :: Networking",
    ],
    entry_points={
        "console_scripts": [
            "tcset=tcconfig.tcset:main",
            "tcdel=tcconfig.tcdel:main",
        ],
    }
)
