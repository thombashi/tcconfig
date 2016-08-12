# encoding: utf-8


def pytest_addoption(parser):
    parser.addoption("--device", default="eth0")
    parser.addoption("--dst-host", default="")
    parser.addoption("--dst-host-ex", default="")
