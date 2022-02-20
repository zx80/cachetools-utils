# convenient makefile

SHELL	= /bin/bash
.ONESHELL:

MODULE	= CacheToolsUtils
F.md	= $(wildcard *.md)
F.pdf	= $(F.md:%.md=%.pdf)

PYTHON	= python
PIP		= venv/bin/pip
PYTEST	= pytest --log-level=debug --capture=tee-sys
PYTOPT	=

.PHONY: check
check: install
	. venv/bin/activate
	type $(PYTHON)
	mypy $(MODULE).py
	flake8 --ignore= $(MODULE).py
	$(PYTEST) $(PYTOPT) test.py

.PHONY: coverage
coverage:
	. venv/bin/activate
	coverage run -m $(PYTEST) $(PYTOPT) test.py
	coverage html $(MODULE).py

.PHONY: clean clean-venv
clean:
	$(RM) -r __pycache__ *.egg-info dist build .mypy_cache .pytest_cache htmlcov
	$(RM) .coverage $(F.pdf)

clean-venv: clean
	$(RM) -r venv

.PHONY: install
install: CacheToolsUtils.egg-info

CacheToolsUtils.egg-info: venv
	$(PIP) install -e .

# for local testing
venv:
	$(PYTHON) -m venv venv
	$(PIP) install wheel mypy flake8 pytest coverage \
		cachetools types-cachetools pymemcache redis types-redis

# generate source and built distribution
dist:
	$(PYTHON) setup.py sdist bdist_wheel

.PHONY: publish
publish: dist
	# provide pypi login/pw or token somewhere…
	twine upload --repository $(MODULE) dist/*

# generate pdf doc
MD2PDF  = pandoc -f markdown -t latex -V papersize:a4 -V geometry:hmargin=2.5cm -V geometry:vmargin=3cm

%.pdf: %.md
	$(MD2PDF) -o $@ $<
