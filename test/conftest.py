# encoding: utf-8


def pytest_addoption(parser):
    parser.addoption("--device", default=None)
    parser.addoption("--dst-host", default="")
    parser.addoption("--dst-host-ex", default="")
