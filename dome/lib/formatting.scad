// ---------------------------------------------------------------------------
// formatting.scad -- exact fixed-point number formatting for data export.
//
// WHY THIS EXISTS
//
// OpenSCAD prints numbers with 6 significant digits and offers no way to ask
// for more. Both of these lose data:
//
//   echo(2551.9524669)        -> ECHO: 2551.95
//   echo(str(2551.9524669))   -> ECHO: "2551.95"
//
// For a picture that is fine. For a machine-readable geometry export it is not:
// a crossing coordinate truncated to 6 significant digits is accurate to about
// 0.01 mm on a 6 m dome and worse on a 12 m one, and the error is silent.
//
// The fix is to never hand a long number to str(). Split it into chunks that
// are each short enough to print exactly, and reassemble them as text.
// `int_str` emits an integer in groups of three digits; `num_str` splits a
// real into its integer part and a scaled fractional part and formats both.
// The result is exact for any magnitude, at the requested number of decimals.
// ---------------------------------------------------------------------------

// Left-pad with zeros to a fixed width.
function _pad0(s, width) = len(s) >= width ? s : _pad0(str("0", s), width);

// A non-negative integer as an exact decimal string, any magnitude.
// Chunks of 3 digits stay well inside the 6-significant-digit printing limit.
function int_str(n) =
    n < 1000
        ? str(n)
        : let (hi = floor(n / 1000))
          str(int_str(hi), _pad0(str(n - hi * 1000), 3));

// A real number as an exact fixed-point decimal string.
// `dp` decimals, half-up rounding, "-0.000000" normalised to "0.000000".
function num_str(x, dp = 6) =
    let (
        a  = abs(x),
        f  = pow(10, dp),
        n  = round(a * f),
        ip = floor(n / f),
        fp = round(n - ip * f),
        sign = (x < 0 && n != 0) ? "-" : ""
    )
    dp <= 0
        ? str(sign, int_str(n))
        : str(sign, int_str(ip), ".", _pad0(int_str(fp), dp));

// Join a list of strings with a separator.
function join(list, sep = ",", i = 0) =
    len(list) == 0 ? ""
    : i >= len(list) - 1 ? str(list[i])
    : str(list[i], sep, join(list, sep, i + 1));

// A list of numbers as joined fixed-point strings.
function num_list_str(list, dp = 6, sep = ";") =
    join([for (x = list) num_str(x, dp)], sep);
