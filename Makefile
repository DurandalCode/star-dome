# Star Dome -- reproducible geometry pipeline.
#
# Everything here runs headless. Nothing needs a GUI, so an agent or CI can
# run the same commands a person does. See docs/architecture.md.

PYTHON  ?= python3
VENV    ?= .venv
VPY      = $(VENV)/bin/python
OUT     ?= exports/model
OPENSCAD ?= /Applications/OpenSCAD-2021.01.app/Contents/MacOS/OpenSCAD

.PHONY: help build report verify test snapshot config connectors weave blender venv clean check scad

help:
	@echo "make build      generate model.json + CSV for every variant into $(OUT)"
	@echo "make report     print derived dimensions for every variant"
	@echo "make verify     check the geometric invariants"
	@echo "make test       run the test suite (needs 'make venv' once)"
	@echo "make snapshot   refresh the committed golden summaries"
	@echo "make config     regenerate configs/variants.scad from variants.toml"
	@echo "make connectors show which connector parts each variant needs"
	@echo "make weave      four-rod node fan geometry and stacking order"
	@echo "make blender    build the 1:1 Blender scene (V=D6) and render a preview"
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

# What connector parts the dome needs, derived from the model rather than
# argued about. Add --json to feed connectors/generate_clamps.py.
weave:
	@$(PYTHON) -m stardome weave --all

connectors:
	@$(PYTHON) -m stardome connectors --all

# Build the 1:1 Blender scene. Layered weave and polylines are required: in
# flat mode every crossing has two rods in the same place, which makes a
# clearance check meaningless.
BLENDER ?= /Applications/Blender.app/Contents/MacOS/Blender
V ?= D6
v = $(shell echo $(V) | tr A-Z a-z)

blender:
	$(PYTHON) -m stardome build $(V) --polylines --weave-mode layered -o $(OUT)
	$(BLENDER) --background --factory-startup --python blender/build_scene.py -- \
		--model $(OUT)/star_dome_$(v).json \
		--out exports/blender/star_dome_$(v).blend \
		--render exports/blender/star_dome_$(v).png

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
