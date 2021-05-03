AUTHOR := thombashi
PACKAGE := tcconfig
DOCS_DIR := docs
DOCS_BUILD_DIR := $(DOCS_DIR)/_build
BUILD_WORK_DIR := _work
PKG_BUILD_DIR := $(BUILD_WORK_DIR)/$(PACKAGE)


.PHONY: build
build:
	@make clean
	@tox -e buildwhl
	ls -lh dist/*

.PHONY: build-remote
build-remote:
	@rm -rf $(BUILD_WORK_DIR)
	@mkdir -p $(BUILD_WORK_DIR)
	@cd $(BUILD_WORK_DIR) && \
		git clone https://github.com/$(AUTHOR)/$(PACKAGE).git --depth 1 && \
		cd $(PACKAGE) && \
		tox -e buildwhl
	ls -lh $(PKG_BUILD_DIR)/dist/*

.PHONY: check
check:
	@tox -e lint
	travis lint

.PHONY: clean
clean:
	@rm -rf $(BUILD_WORK_DIR)
	@tox -e clean

.PHONY: docs
docs:
	@tox -e docs

.PHONY: fmt
fmt:
	@tox -e fmt

.PHONY: readme
readme:
	@tox -e readme

.PHONY: release
release:
	@cd $(PKG_BUILD_DIR) && python setup.py release --sign

.PHONY: setup
setup:
	@pip install --upgrade -e .[test] releasecmd tox
	pip check
