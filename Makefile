# Star Dome -- reproducible geometry pipeline.
#
# Everything here runs headless. Nothing needs a GUI, so an agent or CI can
# run the same commands a person does. See docs/architecture.md.

PYTHON  ?= python3
VENV    ?= .venv
VPY      = $(VENV)/bin/python
OUT     ?= exports/model
OPENSCAD ?= /Applications/OpenSCAD-2021.01.app/Contents/MacOS/OpenSCAD

.PHONY: help build report verify test snapshot config connectors weave entrances doorways interiors covers corridors rods wind clamps blender site sizes camp venv clean check scad

help:
	@echo "make build      generate model.json + CSV for every variant into $(OUT)"
	@echo "make report     print derived dimensions for every variant"
	@echo "make verify     check the geometric invariants"
	@echo "make test       run the test suite (needs 'make venv' once)"
	@echo "make snapshot   refresh the committed golden summaries"
	@echo "make config     regenerate configs/variants.scad from variants.toml"
	@echo "make connectors show which connector parts each variant needs"
	@echo "make weave      four-rod node fan geometry and stacking order"
	@echo "make doorways   the chosen door: which bay, framed by what"
	@echo "make sizes      S, M, L and XL in one scene, every door facing front"
	@echo "make camp       one S, one M and one L round a yard, doors cut open"
	@echo "make entrances  where a doorway fits in each variant, and how big"
	@echo "make interiors  how much floor you can stand on, per variant"
	@echo "make covers     fabric area, and how few gores it sews from"
	@echo "make corridors  a covered corridor on the doorway, and whether it fits"
	@echo "make camp       five domes joined by corridors, laid out and drawn"
	@echo "make rods       how much rod, in what lengths, and what it costs"
	@echo "make wind       SCREENING sail area and hold-down; not a check"
	@echo "make clamps     build every connector into exports/connectors (needs FreeCAD)"
	@echo "make blender    build the 1:1 Blender scene (V=D6) and render a preview"
	@echo "make site       one scene with every variant side by side, at 1:1"
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

# Build every connector the schedule asks for, into exports/connectors/ as
# STEP (open in FreeCAD), STL (drop into a slicer) and FCStd (editable).
# Needs FreeCAD; runs it headless, no GUI.
FREECADCMD ?= /Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd

# Where a door can go. DOOR sets the opening solved for, height then width.
DOOR ?= 1800 700

entrances:
	@$(PYTHON) -m stardome entrance --all --door $(DOOR)

doorways:
	@$(PYTHON) -m stardome doorway --all

interiors:
	@$(PYTHON) -m stardome interior --all

# Fabric area and how few gores it sews from. ROLL is the fabric roll width.
ROLL ?= 1500

covers:
	@$(PYTHON) -m stardome cover --all --roll $(ROLL)

# A covered corridor on the doorway. CORRIDOR is width, height, length in mm.
CORRIDOR ?= 900 1950 3000

# SCREENING ONLY -- no code, no factors, no uplift. See docs/wind.md.
FABRIC ?= oxford_600d
CF ?= 0.5

# The rod half of the shopping list. STOCK is the bar length in mm; leave it
# empty for coil, which has no cutting waste.
STOCK ?= 11800
ROD_PRICE ?=

rods:
	@$(PYTHON) -m stardome rod S M L XL --stock $(STOCK) $(if $(ROD_PRICE),--price $(ROD_PRICE),)

wind:
	@$(PYTHON) -m stardome wind --all --fabric $(FABRIC) --cf $(CF)

corridors:
	@$(PYTHON) -m stardome corridor --all \
		--width $(word 1,$(CORRIDOR)) \
		--height $(word 2,$(CORRIDOR)) \
		--length $(word 3,$(CORRIDOR))

clamps:
	$(PYTHON) -m stardome connectors $(V) --json -o $(OUT)
	$(FREECADCMD) -c "REPO='$(CURDIR)'; VARIANT='$(V)'; p=REPO+'/connectors/generate_clamps.py'; exec(compile(open(p).read(),p,'exec'))"

# Build the 1:1 Blender scene. Layered weave and polylines are required: in
# flat mode every crossing has two rods in the same place, which makes a
# clearance check meaningless.
BLENDER ?= /Applications/Blender.app/Contents/MacOS/Blender
# Blender exits 0 even when a --python script raises. Without this a
# broken scene script leaves the previous render in place, looking current.
BLENDER_RUN = $(BLENDER) --background --factory-startup --python-exit-code 1
V ?= D6
v = $(shell echo $(V) | tr A-Z a-z)

blender:
	$(PYTHON) -m stardome build $(V) --polylines --corridor --weave-mode layered -o $(OUT)
	$(BLENDER_RUN) --python blender/build_scene.py -- \
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

# Every variant in one scene, small to large, each with a 1.75 m figure. The
# comparison is the point: a dome twice as wide is nowhere near twice the
# usable volume, and only standing them together shows it.
# The four sizes anyone is asked to build, each turned so its doorway faces
# the camera, each with a figure standing in that doorway. The question the
# scene answers is not "how big is it" but "does a person get in".
sizes:
	$(PYTHON) -m stardome build --all --polylines --weave-mode layered -o $(OUT)
	$(BLENDER_RUN) --python blender/build_site.py -- \
		--named-only \
		--out exports/blender/sizes.blend \
		--render exports/blender/sizes.png

# One of each of the three sizes anyone camps in, standing round a yard with
# the doorways actually cut out rather than ghosted. This is the picture of
# the thing as built; `make sizes` is the picture of the decisions in it.
# A camp, not a size chart: five domes actually JOINED by corridors. L is the
# hall with three ways out of it, and M takes a fourth on to the last S.
# The layout is solved, not drawn -- a dome has five bays 72 degrees apart, so
# the bearings are quantised and the domes have to be turned to agree.
# CAMP_KIND is hoop or portal.
CAMP_KIND ?= hoop

camp:
	$(PYTHON) -m stardome camp --kind $(CAMP_KIND)
	$(PYTHON) -m stardome camp --kind $(CAMP_KIND) --json -o $(OUT)
	$(PYTHON) -m stardome build S M L --polylines --weave-mode layered -o $(OUT)
	$(BLENDER_RUN) --python blender/build_site.py -- \
		--models $(OUT)/star_dome_d4.json $(OUT)/star_dome_d6.json \
		         $(OUT)/star_dome_d8.json \
		--plan $(OUT)/star_dome_camp.json --hide-cuts \
		--out exports/blender/camp.blend \
		--render exports/blender/camp.png

site:
	$(PYTHON) -m stardome build --all --polylines --weave-mode layered -o $(OUT)
	$(BLENDER_RUN) --python blender/build_site.py -- \
		--dir $(OUT) --gap 3.0 \
		--out exports/blender/site.blend \
		--render exports/blender/site.png

clean:
	rm -rf $(OUT)
