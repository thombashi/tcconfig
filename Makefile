BIN_DIR := $(shell pwd)/bin
DOCS_DIR := docs
DOCS_BUILD_DIR := $(DOCS_DIR)/_build

PYTHON := python3
BIN_CHANGELOG_FROM_RELEASE := $(BIN_DIR)/changelog-from-release


$(BIN_CHANGELOG_FROM_RELEASE):
	GOBIN=$(BIN_DIR) go install github.com/rhysd/changelog-from-release/v3@latest

.PHONY: build
build: clean
	$(PYTHON) -m tox -e buildwhl
	ls -lh dist/*

.PHONY: changelog
changelog: $(BIN_CHANGELOG_FROM_RELEASE)
	$(BIN_CHANGELOG_FROM_RELEASE) > CHANGELOG.md
	cp -a CHANGELOG.md docs/pages/CHANGELOG.md

.PHONY: check
check:
	$(PYTHON) -m tox -e lint

.PHONY: clean
clean:
	rm -rf $(BIN_DIR)
	$(PYTHON) -m tox -e clean

.PHONY: docs
docs:
	$(PYTHON) -m tox -e docs

.PHONY: fmt
fmt:
	$(PYTHON) -m tox -e fmt

.PHONY: readme
readme:
	$(PYTHON) -m tox -e readme

.PHONY: release
release:
	$(PYTHON) -m tox -e release

.PHONY: setup-ci
setup-ci:
	$(PYTHON) -m pip install -q --disable-pip-version-check --upgrade pip
	$(PYTHON) -m pip install -q --disable-pip-version-check --upgrade tox

.PHONY: setup-dev
setup-dev: setup-ci
	$(PYTHON) -m pip install -q --disable-pip-version-check --upgrade -e .[test]
	$(PYTHON) -m pip check

.PHONY: test
test:
	$(PYTHON) -m tox -e py

.PHONY: update-releases-info
update-releases-info:
	@curl -sSL https://api.github.com/repos/thombashi/tcconfig/releases/latest > info/release_latest.json
