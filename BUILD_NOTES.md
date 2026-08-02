# Build Notes — TRANSPORT v1.6

How `bin/trns.exe` and `bin/bsheet.exe` got built on arm64 macOS with
gfortran, and why `Makefile.build` looks the way it does instead of
just using the distribution `Makefile`. Written up for whoever next
has to touch this — see `RUNNING.md` for how to actually run the
binaries once built.

## Toolchain

No `f77` on this machine — Homebrew `gfortran` (16.1.0) instead.
Compiled with:

```
gfortran -g -std=legacy -w -fallow-argument-mismatch -fno-range-check -ffpe-trap=invalid,zero,overflow -fbacktrace -Iinclude -c ...
```

`-std=legacy -w` relaxes gfortran's modern strictness back toward
1990s f77 behavior; `-fallow-argument-mismatch` downgrades
cross-routine argument-type mismatches from hard errors to warnings
(common in code this old); `-fno-range-check` avoids integer-constant
range errors in the random-number code.

`-ffpe-trap=invalid,zero,overflow -fbacktrace` makes the binary abort
with a stack trace on a floating-point invalid-operation, divide-by-
zero, or overflow instead of silently propagating Inf/NaN through
COMMON-block arrays (this codebase's original-era VAX/PowerPC/Absoft
toolchain likely trapped these by default; gfortran does not unless
asked). Both packaged regression decks (`tests/trns.dat`,
`tests/bsheet.dat`) still pass cleanly with trapping on. See "Known
latent bug" below for the reason this matters concretely.

## Fixed: unguarded divide-by-zero in third-order pole-face fringe

`src/fring3.f` (third-order pole-face fringe-field matrix, only
reached when a deck sets `NORD1 .GE. 3` via a `17. 3.` — or higher —
type-code card) computes `EPS = 2.0*H0*APB(2)` (`fring3.f:17`) and
then divides by it at `fring3.f:69` and `fring3.f:127`
(`.../(3.0*EPS)`), with no guard. A bend with a literal zero field
(`H0=0`, i.e. a `4. L 0.0 n` card) flanked by the required `2.`
pole-face cards makes `EPS=0`, producing an unguarded
`H0**3 * (nonzero/0.0)` — floating-point `0 * Inf = NaN` — that
corrupts the shared `U` matrix COMMON block for whatever gets
processed next.

The adjacent bend-body dispatch in `src/thor.f` already guards this
exact case for TYPEC=4 (`thor.f:46`: `IF (H0 .EQ. 0) GO TO 5000`) but
the TYPEC=2 (pole-face) dispatch four lines above it (`thor.f:36`)
calls `FRING3` unconditionally — an asymmetric fix, not a deliberate
design choice. The correct fix mirrors the existing pattern:

```fortran
  200 IF (H0 .EQ. 0) GO TO 5000
      CALL FRING3
      GO TO 5000
```

This is safe because `thor.f:26-27` zeroes the entire `U`/`UL` array
(280 elements) at the top of every `THOR` call before dispatching by
element type, and every single term in `fring3.f` carries an explicit
power of `H0` — so the correct value of every `U(i,j)` this routine
would set is already exactly zero when `H0=0`; skipping the call
doesn't approximate that limit, it *is* that limit.

**Fixed** (commit `4b62f3f`). Verified with two minimal `NORD1=3` test
decks (a bend with pole-face cards, nonzero field, plus `17. 3.`; and
a zero-field companion): the nonzero-field case's output came out
byte-identical before/after — this guard branch is never taken there,
so real third-order calculations don't move — while the zero-field
case, which previously crashed with `SIGILL`/`EXC_BAD_INSTRUCTION` at
the `fdiv` inside `fring3_` under the `-ffpe-trap` build, now runs to
completion with the pole-face contribution correctly zeroed. Both
packaged regression decks still match their reference output modulo
the pre-existing cosmetic diffs noted above.

**Not the cause of the B5 `bsheet.exe` label/drift-loss episode.**
That was independently investigated and traced to something else
entirely: stale archived output files (`B5_neutral-beam_transport_bsheet.txt`,
`_out.txt`) left over from an earlier version of the deck with
different survey coordinates, being compared against a newer edited
deck. Neither `B5_neutral-beam_transport_deck.txt`'s B5D3/B5D4 (both
zero field) nor any other packaged deck actually requests second/third
order, so `FRING3` was never reached in that investigation — the
divide-by-zero above is real but latent, unrelated to what was
originally observed.

## Problem 1: classic-Mac line endings

The whole archive (this being a Mac-era distribution, folder dates
Jan 2004) uses CR-only (`\r`) line endings, no `\n` at all. gfortran
mostly tolerates this — `trcall.f` compiled fine as-is — but at least
one file (`transport.f`, in the sense below) hit a flat `Error: Syntax
error in SUBROUTINE statement` that went away the moment it was piped
through `tr '\r' '\n'`. Rather than track down which files specifically
need it, every source file used in the build is first LF-normalized
into a `build/` staging directory and compiled from there. `src/` and
`original_src/` are never modified in place — they stay as originally
found.

## Problem 2: the Makefile doesn't match the shipped src/

The distribution `Makefile` expects 5 consolidated library sources:

```
TRANSPORT_OBJECTS = transport.o trm.o trin.o trsec.o ranport.o
```

None of `src/transport.f`, `trin.f`, `trm.f`, `trsec.f`, `ranport.f`
exist. What's actually in `src/` is 339 files, one Fortran routine
per file (`accget.f`, `beam.f`, `cab.f`, ... down to `xdate.f`) — this
is a leftover from an old Mac/Absoft MPW build. (The original archive
also shipped a per-routine `.o` object for each of these plus
`transport.exe.make`/`.exe.makeout` build-recipe files pointing at
them, all dated Aug/Nov 2002 — removed when preparing this repo, since
gfortran can't link 2002 PowerPC objects anyway and every `.o` had a
matching `.f` alongside it, so nothing was lost.) The consolidated
5-file layout the Makefile wants survives separately under
`original_src/` (`transport.f`, `trin.f`, `trm.f`, `trsec.f`,
`ranport.f`, plus `MAIN.f`, `TRNSBLK.f`, `TRINBLK.f`, `trm_partial.f`,
an `original Makefile` that's actually just an AFS include-file-copy
script, all dated Nov 2002).

**First attempt (abandoned):** build from `original_src/`'s 5
consolidated files, matching the Makefile literally. This links but
fails with ~40 undefined symbols (`BEAM`, `CAB`, `CABT`, `FINGER`,
`FITCHK`, `FITTIN`, `SOLVE`, `STEPIT`, `MCOUNT`, `MIDENT`, `SPREAD`,
...) — `original_src/` turns out to be an *incomplete* earlier snapshot,
missing routines that exist only in the fuller 339-file tree.
(`MAIN.f` there is byte-identical to `trsec.f`, and `trm_partial.f` is
a smaller/earlier draft of `trm.f` — corroborating that `original_src/` is a
mix of drafts, not a clean release.)

**What actually works:** build every one of the 339 files in `src/`
into a library and link `trcall.o` (the driver) against it directly.
`Makefile.build`'s `LIB_SOURCES` is simply "every `build/*.f` except
the driver programs."

## Problem 3: DLARAN return-type mismatch (real bug)

```
build/randis.f:4:      RANDIS = 2.0*DLARAN(ISEED) - 1.0
Error: Return type mismatch of function 'dlaran' (REAL(4)/REAL(8))
```

`DLARAN` (a LAPACK-derived RNG helper, `dlaran.f`) is declared
`DOUBLE PRECISION FUNCTION`. `RANDIS` (`randis.f`) calls it without
declaring its type, so by Fortran's implicit-typing rules it's called
as a default `REAL`. That's a genuine latent bug in the 1999-era
source — old lax f77 apparently let it slide (probably by luck of
calling convention/register width), gfortran does not. Fixed by
adding `DOUBLE PRECISION DLARAN` to `RANDIS`. (The exact same bug,
same fix, was needed independently in Turtle's `ranport.f` — see that
package's build notes.)

## Problem 4: RCLOCK missing entirely

Link error: `undefined symbol "_rclock_"`, referenced from `rdelmt.o`.
`RCLOCK` doesn't exist anywhere in the 339-file `src/` — genuinely
dropped during whatever historical process split the monolithic files
into per-routine files. Recovered verbatim from
`original_src/ranport.f` (a trivial stub: `XSET=0.0; ISET=IFIX(...)`,
the real `SECNDS(0.0)` VMS-clock call already commented out by
whoever last touched it) and added as `build/rclock.f`.

## Problem 5: BLOCK DATA silently dropped by the linker

This one produced a real runtime bug, not just a build failure.
`trns.exe` linked and ran, but errored immediately on any input:

```
0*** ERROR *** READ ERROR ON LOGICAL UNIT  1, LINE
```

Two things going on here:

1. **`NIN` was 0.** `trnsblk.f`'s `BLOCK DATA TRNSBLK` sets the default
   I/O units (`DATA NIN,NOUT,NPUNCH,NDATA,NPLOT /5,6,4,7,8/`), and
   `trnsprt.f` has `EXTERNAL TRNSBLK, TRINBLK` specifically "so it
   loads properly" per its own comment — but `EXTERNAL` alone doesn't
   make gfortran/`ld` pull an otherwise-unreferenced object out of a
   static archive (`nm` confirmed `trnsprt.o` has no actual reference
   to `_trnsblk_`). With the block data dropped, `NIN` defaulted to 0
   instead of 5, so the first read failed immediately. Fixed by
   forcing `bin/trnsblk.o` and `bin/trinblk.o` directly onto the
   `trns.exe` link line instead of leaving them to be pulled from
   `libtransport.a` on demand.
2. **The error message itself is also buggy**, unrelated to the build:
   `rdline.f`'s `WRITE (NOUT,920) ILINE` supplies one value for a
   two-field `FORMAT` (`'...UNIT ',I2,', LINE ',I4,...`), so the `1`
   printed above is actually `ILINE`, not the unit number — confirmed
   by temporarily adding a debug `WRITE(0,*) 'NIN=',NIN` before the
   read. Left as-is (it's original-source behavior, not something this
   build introduced), but worth knowing if it comes up again.

## bsheet.exe: DATE and MARKCK

`bshm.f` (which defines `SUBROUTINE BSHEET`) needs two routines with
no surviving source anywhere in this archive:

- **`DATE(GRUMPF)`** — a vendor (VAX/VMS, Absoft) runtime-library
  intrinsic, `CHARACTER*9` output in `dd-Mon-yy` format. Confirmed
  against the `22-Jul-99` heading already in `tests/bsheet.out`.
  Reimplemented for real in `build/date_stub.f` using gfortran's
  `DATE_AND_TIME`.
- **`MARKCK`** — genuinely lost, not found anywhere in this archive or
  `original_src/`. By call site (`IF (ALIGN .OR. NUSE .NE. 0) CALL
  MARKCK`, positioned exactly where `TRNSPRT` calls `REVISE`/`REPAIR`
  for the same condition) it looks like a marker/argument consistency
  check tied to alignment-error and `USE`-argument decks — not part of
  the floor-coordinate math itself (that's computed directly in
  `bshm.f`). Stubbed as a documented no-op in `build/markck_stub.f`
  since `tests/bsheet.dat` (the only surviving test deck) never
  exercises `ALIGN`/`USE` and so never actually calls it. **A real
  implementation is still needed before trusting `bsheet.exe` on any
  deck that uses `ALIGN` or `USE`.**

`bshm.o` (and the two stubs) are kept out of the shared
`libtransport.a`/`trns.exe` link — they're BSHEET-specific and adding
them to the general library pulled in the `DATE`/`MARKCK` undefined
symbols even for `trns.exe`, which never needs them.

## Verification

Both binaries were checked against the packaged regression decks —
see `RUNNING.md` for the exact commands and results. Summary:
`trns.exe` matches `tests/trns.out` line-for-line modulo an
expected version-stamp difference and sub-0.01% floating-point drift;
`bsheet.exe` matches `tests/bsheet.out` exactly (all 185 elements,
FRD/station/easting/northing/azimuth fields) with max drift 0.023 ft
over the whole beamline — both consistent with libm/trig precision
differences between the 1999 PowerPC/Absoft compiler and modern
gfortran, not logic errors.
