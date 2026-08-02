#!/usr/bin/env python3
"""Extract beam envelope data from a TRANSPORT output listing and plot it.

Usage: python3 plot_envelope.py [B5_neutral-beam_transport_out.txt]
"""

import re
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

POSITION_RE = re.compile(
    r'^\s*(-?\d+\.\d+)\s+M\s+'
    r'(-?\d+\.\d+)\s+(-?\d+\.\d+)\s+(-?\d+\.\d+)\s+M\s+'
    r'(-?\d+\.\d+)\s+(-?\d+\.\d+)\s+(-?\d+\.\d+)\s+DEG'
)
SIGMA_ROW_RE = re.compile(r'^\s*(-?[\d.]+)\s+(-?[\d.]+)\s+(CM|MR|PC)\b')
ELEMENT_RE = re.compile(
    r'^\s*\(\s*\d+\)\s+\*([A-Z ]+?)\*\s*'
    r'(?:([A-Za-z][\w]*)\s+)?'
    r'(-?[\d.]+)\s+(M|DEG)\b'
)
PASS_MARK_RE = re.compile(r'^1EXP\.')
SURVEY_RE = re.compile(r'16\.\s+(1[6-9])\.\s+-?[\d.]+\s+"([^"]+)"')

# Position-line columns are always X0 (code 16.16), Y0 (16.17), Z0 (16.18), in
# that order. theta0 (16.19) rotates the X0-Z0 pair (the horizontal floor
# plane); Y0 is the vertical bend-plane coordinate, untouched by theta0.


def parse_survey_names(lines):
    """Return {survey code: label}, e.g. {16: 'Easting', 17: 'Height', 18: 'Northing'}."""
    names = {}
    for line in lines:
        m = SURVEY_RE.search(line)
        if m:
            names[int(m.group(1))] = m.group(2)
    return names


def split_passes(lines):
    starts = [i for i, l in enumerate(lines) if PASS_MARK_RE.match(l)]
    if not starts:
        raise ValueError('no "1EXP." pass markers found in file')
    starts.append(len(lines))
    return [lines[starts[i]:starts[i + 1]] for i in range(len(starts) - 1)]


def parse_envelope(pass_lines):
    """Return arrays of S [m], X envelope [cm], Y envelope [cm], and global X0, Y0, Z0 [m]."""
    s_vals, x_env, y_env = [], [], []
    gx_vals, gy_vals, gz_vals = [], [], []
    i, n = 0, len(pass_lines)
    while i < n:
        m = POSITION_RE.match(pass_lines[i])
        if m and i + 6 < n:
            rows = [SIGMA_ROW_RE.match(pass_lines[i + 1 + k]) for k in range(6)]
            if all(rows):
                s_vals.append(float(m.group(1)))
                gx_vals.append(float(m.group(2)))
                gy_vals.append(float(m.group(3)))
                gz_vals.append(float(m.group(4)))
                x_env.append(float(rows[0].group(2)))
                y_env.append(float(rows[2].group(2)))
                i += 7
                continue
        i += 1
    return (np.array(s_vals), np.array(x_env), np.array(y_env),
            np.array(gx_vals), np.array(gy_vals), np.array(gz_vals))


def parse_lattice(pass_lines):
    """Return list of (name, type, s_start, s_end) for beamline elements."""
    elements = []
    s = 0.0
    for line in pass_lines:
        m = ELEMENT_RE.match(line)
        if not m:
            continue
        etype, name, length, unit = m.groups()
        etype = etype.strip()
        length = float(length) if unit == 'M' else 0.0
        elements.append((name or '', etype, s, s + length))
        s += length
    return elements


def find_element(lattice, name):
    for n, _t, s0, s1 in lattice:
        if n == name:
            return s0, s1
    return None


def target_markers(lattice):
    """Return [(label, s), ...] for the B (production) and B* (BSTAR) targets."""
    markers = [('B', 0.0)]
    bstar = find_element(lattice, 'BSTAR')
    if bstar is not None:
        markers.append(('B*', bstar[1]))
    return markers


def target_coords(targets, s, gx, gz):
    """Map (label, s) target markers onto (label, gx, gz) floor-plan coordinates."""
    coords = []
    for name, s_mark in targets:
        idx = int(np.argmin(np.abs(s - s_mark)))
        coords.append((name, gx[idx], gz[idx]))
    return coords


LATTICE_COLORS = {'QUAD': 'tab:red', 'BEND': 'tab:blue'}


def element_coords(lattice, s, gx, gz):
    """Map QUAD/BEND lattice entries onto (name, etype, gx, gz) at their midpoint S."""
    coords = []
    for name, etype, s0, s1 in lattice:
        if etype not in LATTICE_COLORS or s1 <= s0:
            continue
        idx = int(np.argmin(np.abs(s - (s0 + s1) / 2)))
        coords.append((name, etype, gx[idx], gz[idx]))
    return coords


def plot_floorplan(infile, label, tag, gx, gz, target_xy, elem_xy, x_name, z_name, y_name, y_val):
    fig, ax = plt.subplots(figsize=(9, 7))
    ax.plot(gx, gz, color='tab:green', lw=1.5, zorder=1)

    for name, etype, ex, ez in elem_xy:
        ax.plot(ex, ez, 'o', color=LATTICE_COLORS[etype], markersize=7, zorder=2)
        if name:
            ax.annotate(name, xy=(ex, ez), xytext=(7, 0), textcoords='offset points',
                        fontsize=6, va='center')

    for name, tx, tz in target_xy:
        ax.plot(tx, tz, 'ko', markersize=5, zorder=3)
        ax.annotate(name, xy=(tx, tz), xytext=(6, 6), textcoords='offset points',
                    fontsize=9, fontweight='bold')

    ax.set_xlabel(f'{x_name} [m]')
    ax.set_ylabel(f'{z_name} [m]')
    ax.set_aspect('equal', adjustable='datalim')
    ax.set_title(f'B5 neutral-beam line — floor plan — {label}\n'
                 f'({y_name} = {y_val:.3f} m, constant)')
    ax.grid(True, lw=0.3, alpha=0.5)

    fig.tight_layout()
    outpath = infile.with_suffix('').with_name(infile.stem + f'.{tag}.floorplan.png')
    fig.savefig(outpath, dpi=150, bbox_inches='tight')
    print(f'Wrote {outpath}')


def draw_lattice(ax, elements, targets, height=1.0):
    box_style = {'QUAD': 'tab:red', 'BEND': 'tab:blue'}
    for name, etype, s0, s1 in elements:
        color = box_style.get(etype)
        if color is None or s1 <= s0:
            continue
        ax.add_patch(plt.Rectangle((s0, 0.0), s1 - s0, height,
                                    facecolor=color, edgecolor='k', lw=0.5))
        if name:
            ax.text((s0 + s1) / 2, height * 1.15, name,
                     ha='center', va='bottom', fontsize=6, rotation=90)
    for name, s_mark in targets:
        ax.text(s_mark, height * 3.2, name,
                 ha='center', va='top', fontsize=8, fontweight='bold')
    ax.axhline(0, color='k', lw=0.6)
    ax.set_ylim(-0.3, height * 3.2)
    ax.set_yticks([])
    for spine in ('top', 'left', 'right'):
        ax.spines[spine].set_visible(False)


def plot_pass(infile, label, tag, s, xe, ye, lattice):
    fig, (ax_env, ax_lat) = plt.subplots(
        2, 1, figsize=(11, 6), sharex=True,
        gridspec_kw={'height_ratios': [4, 1]},
    )

    ax_env.plot(s, xe, color='tab:red', lw=1.5, label='X envelope')
    ax_env.plot(s, ye, color='tab:blue', lw=1.5, label='Y envelope')
    ax_env.set_ylabel('Envelope [cm]')
    ax_env.axhline(0, color='k', lw=0.5)

    targets = target_markers(lattice)
    for name, s_mark in targets:
        ax_env.axvline(s_mark, color='k', lw=1.0, linestyle=':')
        ax_lat.axvline(s_mark, color='k', lw=1.0, linestyle=':')

    ax_env.legend(loc='upper left', fontsize=8)
    ax_env.set_title(f'B5 neutral-beam line — TRANSPORT beam envelope — {label}')

    draw_lattice(ax_lat, lattice, targets)
    ax_lat.set_xlabel('S [m]')

    fig.tight_layout()
    outpath = infile.with_suffix('').with_name(infile.stem + f'.{tag}.envelope.png')
    fig.savefig(outpath, dpi=150, bbox_inches='tight')
    print(f'Wrote {outpath}')


def main():
    infile = Path(sys.argv[1] if len(sys.argv) > 1 else 'B5_neutral-beam_transport_out.txt')
    lines = infile.read_text().splitlines()
    passes = split_passes(lines)
    if len(passes) < 2:
        print(f'warning: only {len(passes)} pass(es) found, expected 2', file=sys.stderr)

    labels = ['Pass 1 (initial)', 'Pass 2 (final fit)']
    tags = ['pass1', 'pass2']
    survey_names = parse_survey_names(lines)
    x_name = survey_names.get(16, 'X0')
    y_name = survey_names.get(17, 'Y0')
    z_name = survey_names.get(18, 'Z0')

    for idx, p in enumerate(passes[:2]):
        s, xe, ye, gx, gy, gz = parse_envelope(p)
        lattice = parse_lattice(p)
        print(f'{labels[idx]}: {len(s)} envelope points, S {s.min():.3f}-{s.max():.3f} m, '
              f'max X {xe.max():.3f} cm, max Y {ye.max():.3f} cm')
        plot_pass(infile, labels[idx], tags[idx], s, xe, ye, lattice)

        targets = target_markers(lattice)
        target_xy = target_coords(targets, s, gx, gz)
        elem_xy = element_coords(lattice, s, gx, gz)
        plot_floorplan(infile, labels[idx], tags[idx], gx, gz, target_xy, elem_xy,
                        x_name, z_name, y_name, gy[0])


if __name__ == '__main__':
    main()
