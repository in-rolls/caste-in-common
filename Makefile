PY ?= .venv/bin/python
IHDS_SOURCE ?= ../land/data/ihds2/ICPSR_36151/DS0002/36151-0002-Data.rda
NSS_DIR ?= ../land/data/nss77_sch331/csv

.PHONY: setup ihds pilot test lint fmt ci ci-docker
setup:
	python3 -m venv .venv
	$(PY) -m pip install -e '.[dev]'
ihds:
	MPLCONFIGDIR=/tmp/caste-in-common-mpl PYTHONPATH=src $(PY) -m caste_in_common.ihds_pilot --source "$(IHDS_SOURCE)"
pilot:
	MPLCONFIGDIR=/tmp/caste-in-common-mpl PYTHONPATH=src $(PY) -m caste_in_common.pilot --nss-dir "$(NSS_DIR)"
test:
	MPLCONFIGDIR=/tmp/caste-in-common-mpl $(PY) -m pytest -q
lint:
	$(PY) -m black --check src tests
	$(PY) -m isort --check-only src tests
	$(PY) -m flake8 src tests
fmt:
	$(PY) -m black src tests
	$(PY) -m isort src tests
ci: lint test
ci-docker:
	docker run --rm -v "$(CURDIR):/workspace" -w /workspace python:3.13-slim sh -c "pip install -e '.[dev]' && python -m black --check src tests && python -m isort --check-only src tests && python -m flake8 src tests && python -m pytest -q"
