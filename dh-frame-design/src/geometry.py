"""Frame geometry: converts fit targets + component dimensions into coordinates.

Frame coordinate system (used by every file in this study):
  origin  = bottom-bracket centre
  +x      = toward the front wheel (horizontal when the bike stands unloaded on level ground)
  +y      = up
  +z      = toward the rider's LEFT (non-drive side); drive side is -z
  units   = millimetres, degrees
All coordinates are quoted at TOP-OUT (fork and shock fully extended, rider off).
"""
from __future__ import annotations
import numpy as np


def frame_geometry(d: dict) -> dict:
    """d: design dictionary (see designs.py). Returns derived points/lengths."""
    ha = np.radians(d["head_angle"])
    ax = np.array([np.cos(ha), -np.sin(ha)])        # steering axis, pointing down/forward
    nrm = np.array([np.sin(ha), np.cos(ha)])        # perpendicular, pointing forward/up
    R, S = d["reach"], d["stack"]
    rf, rr = d["front_tyre_radius"], d["rear_tyre_radius"]
    L, off, hls = d["fork_axle_to_crown"], d["fork_offset"], d["lower_headset_stack"]
    bbh = d["bb_height"]
    # head tube length follows from stack + BB height + fork length (closed-form)
    htl = (S + off * np.cos(ha) - rf + bbh) / np.sin(ha) - hls - L
    T = np.array([R, S])                            # head tube top centre
    B = T + htl * ax                                # head tube bottom centre
    C = B + hls * ax                                # fork crown race seat
    F = C + L * ax + off * nrm                      # front axle
    ground_y = -bbh
    assert abs((F[1] - rf) - ground_y) < 1e-6
    ya = ground_y + rr                              # rear axle height in frame coords
    A = np.array([-np.sqrt(d["rear_centre"] ** 2 - ya ** 2), ya])
    wb = F[0] - A[0]
    trail = (rf * np.cos(ha) - off) / np.sin(ha)
    return dict(head_tube_len=htl, HT_top=T, HT_bot=B, crown_race=C, front_axle=F,
                rear_axle=A, ground_y=ground_y, wheelbase=wb, front_centre=F[0],
                rear_centre_h=-A[0], bb_drop_front=F[1], bb_drop_rear=A[1],
                trail=trail, steer_axis=ax, steer_normal=nrm)
