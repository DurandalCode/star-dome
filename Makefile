# Star Dome -- reproducible geometry pipeline.
#
# Everything here runs headless. Nothing needs a GUI, so an agent or CI can
# run the same commands a person does. See docs/architecture.md.

PYTHON  ?= python3
VENV    ?= .venv
VPY      = $(VENV)/bin/python
OUT     ?= exports/geometry
OPENSCAD ?= /Applications/OpenSCAD-2021.01.app/Contents/MacOS/OpenSCAD

.PHONY: help build report verify test snapshot config venv clean check scad

help:
	@echo "make build      generate model.json + CSV for every variant into $(OUT)"
	@echo "make report     print derived dimensions for every variant"
	@echo "make verify     check the geometric invariants"
	@echo "make test       run the test suite (needs 'make venv' once)"
	@echo "make snapshot   refresh the committed golden summaries"
	@echo "make config     regenerate configs/variants.scad from variants.toml"
	@echo "make check      verify + test; run this before claiming anything works"
	@echo "make scad       regenerate the OpenSCAD reference export for parity tests"
	@echo "make clean      remove generated exports"

build:
	$(PYTHON) -m stardome build --all -o $(OUT)

report:
	@$(PYTHON) -m stardome report --all

verify:
	@$(PYTHON) -m stardome verify --all

snapshot:
	$(PYTHON) -m stardome snapshot --all

# configs/variants.scad is generated from configs/variants.toml so that the
# OpenSCAD reference implementation and the Python core are fed the same
# numbers. Never edit the .scad by hand.
config:
	$(PYTHON) -m stardome scad-config

venv:
	$(PYTHON) -m venv $(VENV)
	$(VPY) -m pip install --quiet --upgrade pip pytest

test:
	@test -x $(VPY) || { echo "run 'make venv' first"; exit 1; }
	$(VPY) -m pytest tests/ -q

check: verify test

# The OpenSCAD model is a second, independent implementation of the same
# geometry. Regenerating its export lets the parity tests compare the two
# producers field for field.
scad:
	$(OPENSCAD) --version >/dev/null 2>&1 || { echo "OpenSCAD not found at $(OPENSCAD)"; exit 1; }
	$(PYTHON) tools/export_geometry.py

clean:
	rm -rf $(OUT)
