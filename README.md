# TRANSPORT v1.6

A rebuild of TRANSPORT — the charged-particle beam transport design and
fitting program originally developed at SLAC, NAL, and CERN — for modern
arm64 macOS with gfortran.

## Why this repo exists

This is made available as part of a project documenting legacy
experiments. Beamlines for those experiments were designed and tuned
using TRANSPORT input decks written decades ago; this repo exists so
those decks can still be run, largely unchanged, under software that
builds and executes on current hardware. See `RUNNING.md` for how to
build and run it, and `BUILD_NOTES.md` for the full history of what it
took to get a 2002-era, per-routine Fortran source tree building and
matching its original reference output on arm64.

## Warning and disclaimer

This software is provided as-is, with no warranty of correctness,
fitness for a particular purpose, or fitness for any specific
experiment's reconstruction. Neither the maintainers of this repo nor
Fermilab are responsible for results obtained from it, decisions made
using it, or any errors — known or not yet discovered — in its
calculations. `BUILD_NOTES.md` documents one real, silently-corrupting
bug already found and fixed (see the third-order pole-face fringe
section); the fact that it existed undetected for over two decades
should inform how much trust to place in output the maintainers
haven't specifically checked. Verify results independently, especially
for any beamline configuration or feature not already exercised in
`tests/` or discussed in `BUILD_NOTES.md`.

This code will change over time, at whatever pace bugs are found and
fixed — there is no release schedule, and no guarantee that a given
deck's output will be numerically identical between commits. Pin a
specific commit if you need reproducibility, and check
`BUILD_NOTES.md`/`git log` before assuming a past finding still holds.

## Provenance

This is the Fermilab distribution of TRANSPORT, dated Dec 2002 (also
issued as SLAC-R-091/CERN-80-04/NAL-91). `README-A` (and the original
`README`) carry Fermilab's original distribution notice and license —
see those for the actual terms. `ups/transport.table` is likewise part
of the original Fermilab distribution (a UPS product table). None of
that provenance material has been altered; only the build system and
the one documented bug fix (see `BUILD_NOTES.md`) are new.

## Documentation

The reference manuals for the program itself live in `docs/`:

- [`docs/fermilab-nal-091.pdf`](docs/fermilab-nal-091.pdf) / [`docs/CERN-80-04.pdf`](docs/CERN-80-04.pdf) —
  *TRANSPORT: A Computer Program for Designing Charged Particle Beam
  Transport Systems*, K.L. Brown, F. Rothacker, D.C. Carey, Ch. Iselin
  (May 1980), co-issued as SLAC-91 Rev. 3, NAL-91, and CERN-80-04. The
  primary user manual: input deck format, type codes, matrix
  formalism.
- [`docs/SLAC-75.pdf`](docs/SLAC-75.pdf) — the companion SLAC report
  the source code repeatedly cites for underlying derivations (e.g.
  fringe-field integrals, second-order matrix elements).

For this repo specifically:

- [`RUNNING.md`](RUNNING.md) — build and run instructions.
- [`BUILD_NOTES.md`](BUILD_NOTES.md) — how the modern build was put
  together, every portability issue hit along the way, and the one
  real bug found and fixed in the process.
- [`original_src/README.md`](original_src/README.md) — what the
  `original_src/` directory is and why it's kept but unused.
