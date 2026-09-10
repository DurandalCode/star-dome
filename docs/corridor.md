# The covered corridor

```bash
python3 -m stardome corridor D10
make corridors CORRIDOR="900 1950 3000"
```

A corridor is how two domes become a camp rather than two tents. This puts one
on the chosen doorway and checks the thing everyone assumes: **that it fits
through the hole it is attached to.**

There are two kinds, and the second does not replace the first.

| | hoop | portal |
|---|---|---|
| material | bent fibreglass rod | sawn board, 45 × 145 |
| shape | legs + semicircular roof | posts + header + knee braces |
| width | 900 mm | 1500–2000 mm |
| per rib | 4414 mm of rod | 7.1 m of board |
| passes a bare D10 door | yes, whole | no — 1025 mm is the limit |

`--kind hoop` is the default. `--kind portal` is below.

## What the hoop is

A hooped tunnel — a polytunnel. Straight legs to shoulder height, a
semicircular roof over them, fabric across the lot.

    height H = leg + W/2          the roof is a semicircle of radius W/2
    hoop rod = 2*leg + pi*W/2     one bent rod per hoop

Hoops rather than a miniature star dome, for the reason the project keeps
everywhere: a repeated part beats a clever one. Every hoop is the same hoop.

## Two results

### The corridor bends rod far harder than the dome does

Every bow in the dome is bent to the dome radius, and minimum bend radius is
already a live constraint on rod selection (milestone 1). A corridor hoop is
bent to **half its own width**:

| | bend radius | vs the dome |
|---|---|---|
| D6 bow | 3000 mm | — |
| D10 bow | 5000 mm | — |
| 900 mm corridor hoop | **450 mm** | 6.7x tighter than D6, 11.1x than D10 |

The corridor cannot be made of dome stock. It wants thinner rod, and that is a
purchasing decision rather than a drawing one. The report says so in as many
words rather than quietly drawing a hoop nothing will bend to.

### A corridor cannot be bigger than its doorway

The default 900 × 1950 mm corridor, the one sized for the same "carry"
silhouette the doorway defaults to:

| variant | fits | why |
|---|---|---|
| D4 + 1350 skirt | **yes**, 27 mm spare | the skirt is doing all the work |
| D6 bare | no, too tall | 1816 mm of opening; the tallest that passes at 900 wide is 1175 mm, which admits a crawl |
| D8 bare | no, too wide | tall enough, but only 225 mm wide at 1950 mm |
| D10 bare | **yes**, 273 mm spare | |
| D12 bare | **yes**, 789 mm spare | |

Which is the same story the doorway and entrance work already told, arrived at
from the other end: **M and L have no walk-through corridor without a skirt,
for exactly the reason they have no walk-in door.** S has one because of its
skirt, XL because of its size.

The check is not a new rule. The tunnel's cross-section is handed to
`doorway.fit_shape` as a silhouette — the same routine, envelope and rules
that decide whether a person gets through the door. A corridor is just a very
wide, very square person.

## Where it meets the dome

The mouth is the curve where the tunnel meets the cover, and the cover is a
sphere above the base ring and a cylinder through the skirt:

    z >= 0    u = sqrt(Rc^2 - v^2 - z^2)      the sphere
    z <  0    u = sqrt(Rc^2 - v^2)            the skirt cylinder

So the joint is **not a plane cut**. On D6 the mouth reaches from 2378 to 3042
mm from the centre: butt a corridor square against the dome and there is
664 mm of gap at the crown. It gets flatter as the dome grows — 472 mm on D8,
368 on D10 — which is one of the few things about this design that improves
with size.

The mouth is exported as a closed 3D curve for whatever has to be cut to it.

## The roof pinches

A semicircular roof narrows fast near the crown, and heads are near the crown.
900 mm wide needs **1915 mm** of height before the "carry" silhouette's
shoulders *and* head both clear it; at 1900 mm only "walk" gets through. The
default is 1950 mm to keep margin over that threshold.

## The timber portal

```bash
python3 -m stardome corridor D10 --kind portal --width 1800
```

Two posts, a header across them, a knee brace in each top corner. Boards, not
rod — so it is a cut list rather than a bend:

| member | count | length |
|---|---|---|
| post | 2 | 2100 mm |
| header | 1 | 2090 mm |
| knee brace | 2 | 424 mm, both ends at 45° |

7.1 m of board per frame, at 1200 mm centres.

**The braces are not optional.** Three boards pinned at two corners is a
mechanism: it folds along the corridor under any wind. A brace turns each top
corner into a triangle. It costs clear opening to do it — which is the next
point.

### The opening is a trapezoid

The braces cut both top corners at 45°, so what is clear is full width up to
`height − brace_leg`, then chamfered in by the brace leg. At 1800 × 2100 with
300 mm braces: 1800 wide up to 1800 high, 1200 wide at the header.

That shape happens to suit the traffic. A person is wide at the shoulders and
narrower at the head, and so is this. The hoop's semicircular roof starts
narrowing at shoulder height and does not stop — which is why the hoop needs
1915 mm before a "carry" silhouette clears it, and why its head pinch is the
thing that sets its height.

### What it buys, and what it costs

**Buys width.** At head height (1800 mm) an 1800 mm portal is 900 mm to the
centreline against the 900 mm hoop's 424 — more than twice. That is two-way
traffic, or furniture, rather than one more person-shape on the list. Both
kinds pass every standard silhouette at 2100 mm high; the templates simply do
not reach wide enough to show the difference.

**Costs the junction.** A bay narrows toward its head, and the portal demands
full width right up to the braces — where the hoop has already curved in. So
the portal is the *worse* shape for getting through the lancet:

| dome | widest hoop at 1950 | widest portal at 2100 |
|---|---|---|
| S (D4 + 1350) | 900 mm | 725 mm |
| M (D6 bare) | 1175 mm tall max | nothing |
| L (D8 bare) | — | nothing |
| XL (D10 bare) | 900 mm passes whole | 1025 mm |
| D12 bare | — | 1675 mm |

A 1800 mm portal passes no dome in the family whole. Its posts land on the
bows rather than inside the bay, so **the junction needs a detail that does
not exist yet** — trim the corridor down to the bay, or raise the dome:

    D6   1800 mm of skirt
    D8   1300 mm
    D10   700 mm
    D4   not at any skirt under 3 m

None of which makes the portal wrong. A person walks from the corridor
through the doorway unaffected — D10's door admits every silhouette including
the 2.2 m character. It bites on carrying something through in one movement,
and on what holds the corridor up where it meets the dome. That interface is
milestone 5.

## In the scene

`make blender` attaches one and draws it: hoops as tubes, skin translucent. A
corridor the model says will not pass its own doorway is still drawn — seeing
why it fails is the point — but in the red this scene already uses for "this
is not really there". On D6 you can see the arch standing proud of the
opening.

## What this does not do

No structure. Wind on a tunnel, hoop footings, the joint at the dome and how
the fabric transfers load are milestones 5 and 8. Shape, fit and quantities
only.
