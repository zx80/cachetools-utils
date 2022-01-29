# convenient makefile

.ONESHELL:
MODULE	= CacheToolsUtils.py
F.md	= $(wildcard *.md)
F.pdf	= $(F.md:%.md=%.pdf)

PYTEST	= pytest --log-level=debug --capture=tee-sys
PYTOPT	=

.PHONY: check
check: venv
	. venv/bin/activate
	type python3
	mypy $(MODULE)
	flake8 --ignore=E402,E501,F401 $(MODULE)
	$(PYTEST) $(PYTOPT) test.py

.PHONY: coverage
coverage:
	coverage run -m $(PYTEST) $(PYTOPT) test.py
	coverage html $(MODULE)

.PHONY: clean clean-venv
clean:
	$(RM) -r __pycache__ */__pycache__ *.egg-info dist build .mypy_cache .pytest_cache htmlcov
	$(RM) .coverage $(F.pdf)

clean-venv: clean
	$(RM) -r venv

.PHONY: install
install:
	pip3 install -e .

# for local testing
venv:
	python3 -m venv venv
	venv/bin/pip3 install -e .
	venv/bin/pip3 install wheel mypy flake8 pytest coverage \
		cachetools types-cachetools pymemcache redis types-redis

# generate source and built distribution
dist:
	python3 setup.py sdist bdist_wheel

.PHONY: publish
publish: dist
	# provide pypi login/pw or token somewhere…
	twine upload --repository CacheToolsUtils dist/*

# generate pdf doc
MD2PDF  = pandoc -f markdown -t latex -V papersize:a4 -V geometry:hmargin=2.5cm -V geometry:vmargin=3cm

%.pdf: %.md
	$(MD2PDF) -o $@ $<
