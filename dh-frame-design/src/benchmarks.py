"""Benchmark bikes: published geometry and ESTIMATED leverage curves (see sources/)."""
from __future__ import annotations
import numpy as np


def linear_lr_from_progression(travel, stroke, prog):
    """Leverage curve assumed linear in wheel travel, fixed by travel, stroke and progression."""
    lr0 = travel * np.log(1 / (1 - prog)) / (stroke * prog)
    return lr0, lr0 * (1 - prog)


def sweep_from_lr(travel, lr0, lr1, n=401):
    z = np.linspace(0, travel, n)
    lr = lr0 + (lr1 - lr0) * z / travel
    s = np.concatenate([[0], np.cumsum(0.5 * (1 / lr[1:] + 1 / lr[:-1]) * np.diff(z))])
    return dict(travel=z, lr=lr, stroke=s)


SENDER = dict(
    name="Canyon Sender CFR (Gen 3) size M, +8 mm cup, BB high",
    reach=476.0, stack=630.0, head_angle=63.0, rear_centre=438.0, wheelbase=1281.0,
    head_tube=105.0, fork_a2c=605.0, fork_offset=52.0, front_radius=375.0, rear_radius=356.0,
    bb_height=352.0, travel=200.0, stroke=75.0, frame_mass=4.614,
    lr=dict(method="estimated: linear curve from published progression 32.7 % and 200/75 mm",
            curve=linear_lr_from_progression(200.0, 75.0, 0.327)),
    lr_alt=dict(method="estimated: as above with the 37 % chip", curve=linear_lr_from_progression(200.0, 75.0, 0.37)),
)

SUPREME = dict(
    name="Commencal Supreme DH V5 size L, Low",
    reach=484.0, stack=649.0, head_angle=63.3, rear_centre=454.0, wheelbase=1311.0,
    head_tube=112.0, fork_a2c=605.0, fork_offset=52.0, front_radius=375.0, rear_radius=356.0,
    bb_height=None, travel=220.0, stroke=75.0, frame_mass=5.3,
    lr=dict(method="estimated: third-party reconstruction (Linkage Design, 2023), 3.45 -> 2.6 over 220 mm",
            curve=(3.45, 2.60)),
)
