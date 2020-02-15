def pytest_addoption(parser):
    parser.addoption("--device", default=None)
    parser.addoption("--local-host", default="")
    parser.addoption("--dst-host", default="")
    parser.addoption("--dst-host-ex", default="")
