PACKAGE := tcconfig
DOCS_DIR := docs
DOCS_BUILD_DIR := $(DOCS_DIR)/_build


.PHONY: build
build:
	@make clean
	@python setup.py sdist bdist_wheel
	@twine check dist/*
	@python setup.py clean
	ls -lh dist/*

.PHONY: check
check:
	python setup.py check
	travis lint
	pylama

.PHONY: clean
clean:
	@rm -rf $(PACKAGE)-*.*.*/ \
		$(DOCS_BUILD_DIR) \
		dist/ \
		pip-wheel-metadata/ \
		.eggs/ \
		.pytest_cache/ \
		.tox/ \
		*.egg-info/
	@python setup.py clean
	@find . -name "__pycache__" -type d -exec rm -rf "{}" \;
	@find . -name "*.pyc" -delete
	@find . -not -path '*/\.*' -type f | grep -E .+\.py\.[a-z0-9]{32,}\.py$ | xargs -r rm

.PHONY: docs
docs:
	@python setup.py build_sphinx --source-dir=$(DOCS_DIR)/ --build-dir=$(DOCS_BUILD_DIR) --all-files

.PHONY: fmt
fmt:
	@tox -e fmt

.PHONY: readme
readme:
	@tox -e readme

.PHONY: release
release:
	@python setup.py release --sign
	@make clean
