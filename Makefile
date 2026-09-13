# Star Dome -- reproducible geometry pipeline.
#
# Everything here runs headless. Nothing needs a GUI, so an agent or CI can
# run the same commands a person does. See docs/architecture.md.

PYTHON  ?= python3
VENV    ?= .venv
VPY      = $(VENV)/bin/python
OUT     ?= exports/model
OPENSCAD ?= /Applications/OpenSCAD-2021.01.app/Contents/MacOS/OpenSCAD

.PHONY: help build report verify test snapshot config connectors weave assembly tolerance entrances doorways interior spans bom camp lineups covers attachment corridors clamps blender fitted site sizes camp venv clean check scad

help:
	@echo "make build      generate model.json + CSV for every variant into $(OUT)"
	@echo "make report     print derived dimensions for every variant"
	@echo "make verify     check the geometric invariants"
	@echo "make test       run the test suite (needs 'make venv' once)"
	@echo "make snapshot   refresh the committed golden summaries"
	@echo "make config     regenerate configs/variants.scad from variants.toml"
	@echo "make connectors show which connector parts each variant needs"
	@echo "make weave      four-rod node fan geometry and stacking order"
	@echo "make assembly   the order the bows go up in, and what it costs"
	@echo "make tolerance  how accurately the ground, rods and marks must be measured"
	@echo "make doorways   the chosen door: which bay, framed by what"
	@echo "make sizes      S, M, L and XL in one scene, every door facing front"
	@echo "make lineup     one of each size in a row, covered and fitted"
	@echo "make camp       domes joined by corridors, from configs/camps.toml"
	@echo "make entrances  where a doorway fits in each variant, and how big"
	@echo "make interiors  how much floor you can stand on, per variant"
	@echo "make covers     fabric area, and how few gores it sews from"
	@echo "make attachment what holds the cover on, and on what"
	@echo "make corridors  a covered corridor on the doorway, and whether it fits"
	@echo "make spans      the longest unsupported span, and the ceiling it sets"
	@echo "make bom        everything one dome is made of, counted in one place"
	@echo "make clamps     build every connector into exports/connectors (needs FreeCAD)"
	@echo "make blender    build the 1:1 Blender scene (V=D6) and render a preview"
	@echo "make fitted     the same dome with every connector fitted (V=M)"
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

# Which bow goes up when. The number that matters is threadings: how many
# times a bow has to be passed UNDER one already standing.
assembly:
	@$(PYTHON) -m stardome assembly --all

# What the tape measure has to achieve. Sigmas are assumptions -- override
# with GROUND=, CUT=, MARK= once someone has measured their own tape.
GROUND ?= 10
CUT ?= 3
MARK ?= 3

tolerance:
	@$(PYTHON) -m stardome tolerance --all --ground $(GROUND) --cut $(CUT) --mark $(MARK)

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

# What holds the cover on, and on what. HEM is the fabric turned under at the
# base edge; TAIL is the webbing left past each foot for tensioning.
HEM  ?= 60
TAIL ?= 300

attachment:
	@$(PYTHON) -m stardome attachment --all --hem $(HEM) --strap-tail $(TAIL)

# A covered corridor on the doorway. CORRIDOR is width, height, length in mm.
CORRIDOR ?= 900 1950 3000

corridors:
	@$(PYTHON) -m stardome corridor --all \
		--width $(word 1,$(CORRIDOR)) \
		--height $(word 2,$(CORRIDOR)) \
		--length $(word 3,$(CORRIDOR))

# The longest unsupported span and the scaling law on it. HOLDS is what counts
# as holding a bow: 'lashed' (feet and tie marks, the conservative reading) or
# 'contact' (every crossing clamped).
HOLDS ?= lashed

spans:
	@$(PYTHON) -m stardome span --all --holds $(HOLDS) --clamps

# Everything one dome is made of. PARTS is where the built connector meshes
# are: their solid volume is read off them, so the plastic column is present
# after 'make clamps' and honestly absent before it.
PARTS ?= exports/connectors

bom:
	@$(PYTHON) -m stardome bom --all --parts $(PARTS)

clamps:
	$(PYTHON) -m stardome connectors $(V) --json -o $(OUT)
	$(FREECADCMD) -c "REPO='$(CURDIR)'; VARIANT='$(v)'; p=REPO+'/connectors/generate_clamps.py'; exec(compile(open(p).read(),p,'exec'))"

# Build the 1:1 Blender scene. Layered weave and polylines are required: in
# flat mode every crossing has two rods in the same place, which makes a
# clearance check meaningless.
BLENDER ?= /Applications/Blender.app/Contents/MacOS/Blender
# Blender exits 0 even when a --python script raises. Without this a
# broken scene script leaves the previous render in place, looking current.
BLENDER_RUN = $(BLENDER) --background --factory-startup --python-exit-code 1
V ?= D6
# S, M, L and XL are aliases; the geometry is filed under D4, D6, D8 and D10,
# and so are every model.json and schedule. Ask the model rather than lowering
# the case of whatever was typed, or `make fitted V=M` looks for d6 under the
# name m and finds nothing.
v = $(shell $(PYTHON) -c "from stardome import config; print(config.resolve('$(V)').lower())")

blender:
	$(PYTHON) -m stardome build $(V) --polylines --corridor --weave-mode layered -o $(OUT)
	$(BLENDER_RUN) --python blender/build_scene.py -- \
		--model $(OUT)/star_dome_$(v).json \
		--out exports/blender/star_dome_$(v).blend \
		--render exports/blender/star_dome_$(v).png

# The dome with every connector fitted, at 1:1. Three things have to line up
# for this to mean anything, and each is a separate command:
#
#   the model must be WOVEN -- layered spreads a crossing over 140 mm and a
#     connector stack is 10, so a part drawn on it would float;
#   the schedule must be regenerated, because it carries where each part goes
#     and which way up, and that is derived from the weave;
#   the parts must actually be built, or there is nothing to place.
#
# What no generator builds yet is blocked in, in red. 57 of M's 107 connectors
# are still in that state and the picture says so.
fitted:
	$(PYTHON) -m stardome build $(V) --polylines --weave-mode woven -o $(OUT)
	$(PYTHON) -m stardome connectors $(V) --json -o $(OUT)
	$(FREECADCMD) -c "REPO='$(CURDIR)'; VARIANT='$(v)'; p=REPO+'/connectors/generate_clamps.py'; exec(compile(open(p).read(),p,'exec'))"
	$(BLENDER_RUN) --python blender/build_scene.py -- \
		--model $(OUT)/star_dome_$(v).json \
		--connectors real --hide-cuts \
		--out exports/blender/fitted_$(v).blend \
		--render exports/blender/fitted_$(v).png \
		--shots exports/shots

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
# One of each size in a row, covered and fitted. It is a lineup, not a camp:
# nothing in it is joined to anything. `make camp` is the camp.
#
# Woven, not layered: the connectors go on the rods, and layered spreads a
# crossing over more than a connector stack is tall. What has no exported mesh
# is reported and left out -- run `make clamps V=S`, `V=M`, `V=L` for the lot.
lineup:
	$(PYTHON) -m stardome build S M L --polylines --weave-mode woven -o $(OUT)
	$(PYTHON) -m stardome connectors S M L --json -o $(OUT)
	$(BLENDER_RUN) --python blender/build_site.py -- \
		--models $(OUT)/star_dome_d4.json $(OUT)/star_dome_d6.json $(OUT)/star_dome_d8.json \
		--camp 4.0 --gap 3.0 --hide-cuts \
		--cover --connectors real \
		--out exports/blender/lineup.blend \
		--render exports/blender/lineup.png

# A camp: domes joined by corridors, laid out from configs/camps.toml. CAMP is
# which one. FLAGS adds --connectors real once `make clamps` has run for every
# variant the plan uses.
CAMP ?= yard
# One pair of figures, not one per dome: eight domes would stand sixteen
# people in eight doorways, and the scene is about the camp.
CAMP_FLAGS ?= --cover --figures one
# What joins the domes: hoop (bent rod, 900 mm) or portal (timber P-frames,
# 1800 mm). See docs/corridor.md.
CAMP_KIND ?= hoop

camp:
	$(PYTHON) -m stardome build --all --polylines --weave-mode woven -o $(OUT)
	$(PYTHON) -m stardome camp $(CAMP) --kind $(CAMP_KIND) --json -o $(OUT)
	$(PYTHON) -m stardome camp $(CAMP) --kind $(CAMP_KIND)
	$(BLENDER_RUN) --python blender/build_site.py -- \
		--dir $(OUT) --plan $(OUT)/$(CAMP)/camp.json \
		--hide-cuts --no-labels $(CAMP_FLAGS) \
		--out exports/blender/camp_$(CAMP).blend \
		--render exports/blender/camp_$(CAMP).png

site:
	$(PYTHON) -m stardome build --all --polylines --weave-mode layered -o $(OUT)
	$(BLENDER_RUN) --python blender/build_site.py -- \
		--dir $(OUT) --gap 3.0 \
		--out exports/blender/site.blend \
		--render exports/blender/site.png

clean:
	rm -rf $(OUT)
