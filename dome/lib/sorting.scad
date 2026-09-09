// ---------------------------------------------------------------------------
// sorting.scad -- deterministic sorting, so generated IDs are stable.
//
// OpenSCAD has no built-in sort. The geometry report needs one: node and
// crossing IDs must depend on where things are in space, not on the order a
// nested loop happened to visit them, or the IDs would shuffle the next time
// someone reorders a list comprehension.
//
// Elements are [key, value] pairs where `key` is a VECTOR of numbers compared
// lexicographically. That covers "sort by height, then by azimuth" without
// packing several quantities into one float and hoping the precision holds.
//
// Merge sort: O(n log n), no mutation, and stable -- equal keys keep their
// original relative order, which matters because it is the last thing keeping
// the output deterministic when two items genuinely tie.
// ---------------------------------------------------------------------------

// Lexicographic comparison of two key vectors.
// Returns -1 if a sorts before b, 1 if after, 0 if equal.
function key_cmp(a, b, i = 0) =
    i >= len(a) || i >= len(b) ? 0
    : a[i] < b[i] ? -1
    : a[i] > b[i] ?  1
    : key_cmp(a, b, i + 1);

// Merge two already-sorted lists of [key, value] pairs.
// `<=` on the comparison keeps this stable: on a tie the left list wins.
function _merge(a, b, i = 0, j = 0) =
    i >= len(a) ? [for (k = [j : 1 : len(b) - 1]) b[k]]
    : j >= len(b) ? [for (k = [i : 1 : len(a) - 1]) a[k]]
    : key_cmp(a[i][0], b[j][0]) <= 0
        ? concat([a[i]], _merge(a, b, i + 1, j))
        : concat([b[j]], _merge(a, b, i, j + 1));

// Sort a list of [key_vector, value] pairs.
function sort_pairs(list) =
    len(list) <= 1 ? list
    : let (
        mid = floor(len(list) / 2),
        left  = [for (i = [0 : 1 : mid - 1]) list[i]],
        right = [for (i = [mid : 1 : len(list) - 1]) list[i]]
      )
      _merge(sort_pairs(left), sort_pairs(right));

// Sort and return just the values.
function sorted_values(list) = [for (p = sort_pairs(list)) p[1]];

// Round to a fixed number of decimals. Used to build comparison keys and
// grouping signatures so that two quantities that are equal in exact arithmetic
// do not end up in different buckets because of floating-point noise.
function quantize(x, decimals = 6) =
    let (f = pow(10, decimals)) round(x * f) / f;
