# convenient makefile

SHELL	= /bin/bash
.ONESHELL:

MODULE	= CacheToolsUtils
F.md	= $(wildcard *.md)
F.pdf	= $(F.md:%.md=%.pdf)


# cleanup and environment

.PHONY: clean
clean:
	$(RM) -r __pycache__ *.egg-info dist build .mypy_cache .pytest_cache htmlcov .ruff_cache
	$(RM) .coverage $(F.pdf)
	$(MAKE) -C docs clean

.PHONY: clean.venv
clean.venv: clean
	$(RM) -r venv

.PHONY: clean.dev
clean.dev: clean.venv

# venv for local testing
PYTHON	= python
PIP		= venv/bin/pip

# tmp workaround for python 3.13t tests
DEPS    = doc,dev,pub,tests,crypt

venv:
	$(PYTHON) -m venv venv
	$(PIP) install --upgrade pip
	$(PIP) install -e .[$(DEPS)]

.PHONY: dev
dev: venv

#
# Tests
#
PYTEST	= pytest --log-level=debug --capture=tee-sys
PYTOPT	=

.PHONY: check
check: check.mypy check.pyright check.flake8 check.pytest check.coverage check.docs

.PHONY: check.mypy
check.mypy: venv
	source venv/bin/activate
	mypy $(MODULE).py

.PHONY: check.pyright
check.pyright: venv
	source venv/bin/activate
	pyright $(MODULE).py

IGNORE  = E226,E227,E501

.PHONY: check.flake8
check.flake8: venv
	source venv/bin/activate
	flake8 --ignore=E129,W504,$(IGNORE) $(MODULE).py

.PHONY: check.ruff
check.ruff: venv
	source venv/bin/activate
	ruff check --ignore=$(IGNORE) $(MODULE).py

.PHONY: check.black
check.black: venv
	source venv/bin/activate
	black --check $(MODULE).py

.PHONY: check.pytest
check.pytest: venv
	source venv/bin/activate
	$(PYTEST) $(PYTOPT) test.py

.PHONY: check.coverage
check.coverage: venv
	source venv/bin/activate
	coverage run -m $(PYTEST) $(PYTOPT) test.py
	# coverage html $(MODULE).py
	coverage report --fail-under=100 --precision=1 --show-missing --include=CacheToolsUtils.py

.PHONY: check.docs
check.docs: venv
	source venv/bin/activate
	pymarkdown -d MD013 scan *.md */*.md
	sphinx-lint docs/

.PHONY: docs
docs: venv
	source venv/bin/activate
	make -C docs html

.PHONY: install
install: $(MODULE).egg-info
	type $(PYTHON)

$(MODULE).egg-info: venv
	$(PIP) install -e .

# generate source and built distribution
dist: venv
	source venv/bin/activate
	$(PYTHON) -m build

.PHONY: publish
publish: dist
	# provide pypi login/pw or token somewhere…
	echo venv/bin/twine upload dist/*

# generate pdf doc
MD2PDF  = pandoc -f markdown -t latex -V papersize:a4 -V geometry:hmargin=2.5cm -V geometry:vmargin=3cm

%.pdf: %.md
	$(MD2PDF) -o $@ $<
