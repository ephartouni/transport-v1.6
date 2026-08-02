# original_src/

An earlier, incomplete snapshot of the TRANSPORT source, kept for historical
reference only — **not used by the current build** (see `Makefile.build` and
`../BUILD_NOTES.md` at the repo root).

## What this is

The distribution `Makefile` at the repo root expects five consolidated
library sources:

```
TRANSPORT_OBJECTS = transport.o trm.o trin.o trsec.o ranport.o
```

This directory is where those five files (`transport.f`, `trin.f`, `trm.f`,
`trsec.f`, `ranport.f`) actually exist, along with `MAIN.f`, `TRNSBLK.f`,
`TRINBLK.f`, `trm_partial.f`, and an `original Makefile` (which turns out to
be an AFS include-file-copy script, not a real Makefile) — 85 files in all,
dated Nov 2002.

`MAIN.f` here is byte-identical to `trsec.f`, and `trm_partial.f` is a
smaller/earlier draft of `trm.f` — this snapshot is a mix of drafts, not a
clean release.

## Why it's not used

Building from these five consolidated files (matching the distribution
`Makefile` literally) links but fails with roughly 40 undefined symbols
(`BEAM`, `CAB`, `CABT`, `FINGER`, `FITCHK`, `FITTIN`, `SOLVE`, `STEPIT`,
`MCOUNT`, `MIDENT`, `SPREAD`, ...). The routines behind those symbols only
exist in the fuller, one-routine-per-file tree at `../src/` (339 files,
originally split for an old Mac/Absoft MPW build — see `../src/*.exe.make`).

The current build (`../Makefile.build`) compiles every file in `../src/`
into a library and links the driver programs against that instead. This
directory is retained purely so the "why not just use the five files the
Makefile expects" question has a documented, reproducible answer.
