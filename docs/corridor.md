# The covered corridor

```bash
python3 -m stardome corridor D10
make corridors CORRIDOR="900 1950 3000"
```

A corridor is how two domes become a camp rather than two tents. This puts one
on the chosen doorway and checks the thing everyone assumes: **that it fits
through the hole it is attached to.**

## What it is

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
