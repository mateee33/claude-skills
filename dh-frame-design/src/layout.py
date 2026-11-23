"""Side-view layout helpers: structure centre lines, clearances, drawing."""
from __future__ import annotations
import numpy as np
from geometry import frame_geometry


def structure_lines(d, g):
    ax = g["steer_axis"]
    T, B = g["HT_top"], g["HT_bot"]
    dt_top = B - 38.0 * ax            # down-tube axis meets the head tube 38 mm above its lower end
    tt_top = T + 30.0 * ax            # top-tube axis meets the head tube 30 mm below its upper end
    return dict(head_tube=(T, B),
                down_tube=(np.array(d["down_tube_end"], float), dt_top),
                top_tube=(np.array(d["top_tube_end"], float), tt_top),
                seat_mast=(np.array(d["seat_mast"][0], float), np.array(d["seat_mast"][1], float)))


def dist_point_segment(p, a, b):
    ab = b - a
    t = np.clip(np.dot(p - a, ab) / np.dot(ab, ab), 0, 1)
    return np.linalg.norm(p - (a + t * ab))


def signed_height(p, a, b):
    """Signed perpendicular distance of p from line a->b (positive on the left of a->b)."""
    t = (b - a) / np.linalg.norm(b - a)
    return t[0] * (p - a)[1] - t[1] * (p - a)[0]
