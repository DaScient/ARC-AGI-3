"""
ARC Domain-Specific Language (DSL)
===================================

A catalog of primitive grid-transformation functions that serve as the
vocabulary from which candidate programs are assembled.

Each primitive has the signature::

    fn(grid: Grid, **kwargs) -> Grid

and is registered in DSLRegistry so the synthesiser can enumerate them.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Callable, Dict, List, Optional, Tuple

import numpy as np

Grid = List[List[int]]
DSLFunction = Callable[..., Grid]


def _to_np(grid: Grid) -> np.ndarray:
    return np.array(grid, dtype=int)


def _to_list(arr: np.ndarray) -> Grid:
    return arr.tolist()


# ---------------------------------------------------------------------------
# Primitive transformations
# ---------------------------------------------------------------------------

def identity(grid: Grid) -> Grid:
    """Return the grid unchanged."""
    return deepcopy(grid)


def rotate_90(grid: Grid) -> Grid:
    """Rotate the grid 90° clockwise."""
    return _to_list(np.rot90(_to_np(grid), k=-1))


def rotate_180(grid: Grid) -> Grid:
    """Rotate the grid 180°."""
    return _to_list(np.rot90(_to_np(grid), k=2))


def rotate_270(grid: Grid) -> Grid:
    """Rotate the grid 270° clockwise (= 90° counter-clockwise)."""
    return _to_list(np.rot90(_to_np(grid), k=1))


def flip_horizontal(grid: Grid) -> Grid:
    """Reflect the grid left-right."""
    return _to_list(np.fliplr(_to_np(grid)))


def flip_vertical(grid: Grid) -> Grid:
    """Reflect the grid top-bottom."""
    return _to_list(np.flipud(_to_np(grid)))


def flip_diagonal(grid: Grid) -> Grid:
    """Transpose the grid (reflect over the main diagonal)."""
    return _to_list(_to_np(grid).T)


def flip_anti_diagonal(grid: Grid) -> Grid:
    """Reflect over the anti-diagonal."""
    return _to_list(np.rot90(np.fliplr(_to_np(grid)), k=2))


def color_replace(grid: Grid, *, source: int, target: int) -> Grid:
    """Replace every occurrence of *source* color with *target* color."""
    arr = _to_np(grid).copy()
    arr[arr == source] = target
    return _to_list(arr)


def color_swap(grid: Grid, *, color_a: int, color_b: int) -> Grid:
    """Swap two colors throughout the grid."""
    arr = _to_np(grid).copy()
    tmp = arr.copy()
    arr[tmp == color_a] = color_b
    arr[tmp == color_b] = color_a
    return _to_list(arr)


def fill_background(grid: Grid, *, background: int = 0, fill: int = 0) -> Grid:
    """Replace all cells equal to *background* with *fill*."""
    arr = _to_np(grid).copy()
    arr[arr == background] = fill
    return _to_list(arr)


def crop_to_content(grid: Grid, *, background: int = 0) -> Grid:
    """Crop the grid to its non-background bounding box."""
    arr = _to_np(grid)
    mask = arr != background
    rows = np.any(mask, axis=1)
    cols = np.any(mask, axis=0)
    if not rows.any():
        return [[background]]
    r0, r1 = int(np.argmax(rows)), int(len(rows) - 1 - np.argmax(rows[::-1]))
    c0, c1 = int(np.argmax(cols)), int(len(cols) - 1 - np.argmax(cols[::-1]))
    return _to_list(arr[r0: r1 + 1, c0: c1 + 1])


def tile(grid: Grid, *, rows: int = 2, cols: int = 2) -> Grid:
    """Tile the grid *rows* × *cols* times."""
    arr = _to_np(grid)
    return _to_list(np.tile(arr, (rows, cols)))


def upscale(grid: Grid, *, factor: int = 2) -> Grid:
    """Upscale each cell into a *factor* × *factor* block."""
    arr = _to_np(grid)
    return _to_list(np.kron(arr, np.ones((factor, factor), dtype=int)))


def downscale(grid: Grid, *, factor: int = 2) -> Grid:
    """Downscale by taking the top-left of each *factor* × *factor* block."""
    arr = _to_np(grid)
    H, W = arr.shape
    new_H, new_W = H // factor, W // factor
    return _to_list(arr[:new_H * factor:factor, :new_W * factor:factor])


def pad(grid: Grid, *, top: int = 1, bottom: int = 1, left: int = 1, right: int = 1, fill: int = 0) -> Grid:
    """Pad the grid with *fill* on each side."""
    arr = _to_np(grid)
    return _to_list(np.pad(arr, ((top, bottom), (left, right)), constant_values=fill))


def gravity(grid: Grid, *, direction: str = "down", background: int = 0) -> Grid:
    """
    Apply gravity: non-background cells "fall" in the given direction.

    Parameters
    ----------
    direction : {"down", "up", "left", "right"}
    background : int
        Color treated as empty space.
    """
    arr = _to_np(grid).copy()
    direction = direction.lower()

    def _fall_column(col: np.ndarray) -> np.ndarray:
        non_bg = col[col != background]
        bg_cells = np.full(len(col) - len(non_bg), background, dtype=int)
        if direction == "down":
            return np.concatenate([bg_cells, non_bg])
        return np.concatenate([non_bg, bg_cells])  # "up"

    if direction in ("down", "up"):
        for c in range(arr.shape[1]):
            arr[:, c] = _fall_column(arr[:, c])
    elif direction in ("left", "right"):
        arr = arr.T
        for c in range(arr.shape[1]):
            arr[:, c] = _fall_column(arr[:, c])
        arr = arr.T
        if direction == "right":
            arr = np.fliplr(arr)
            for c in range(arr.shape[1]):
                arr[:, c] = _fall_column(arr[:, c])
            arr = np.fliplr(arr)
    return _to_list(arr)


def move_object(
    grid: Grid,
    *,
    color: int,
    dr: int = 0,
    dc: int = 0,
    background: int = 0,
) -> Grid:
    """Translate all cells of a given *color* by (dr, dc)."""
    arr = _to_np(grid).copy()
    H, W = arr.shape
    src_mask = arr == color
    result = arr.copy()
    result[src_mask] = background
    rows, cols = np.where(src_mask)
    for r, c in zip(rows, cols):
        nr, nc = int(r) + dr, int(c) + dc
        if 0 <= nr < H and 0 <= nc < W:
            result[nr, nc] = color
    return _to_list(result)


def mirror_complete(grid: Grid, *, axis: str = "V", background: int = 0) -> Grid:
    """
    Complete a partial reflection.

    Takes all non-background cells from one half and mirrors them to the
    other half.

    Parameters
    ----------
    axis : {"V", "H"}  — vertical or horizontal axis.
    """
    arr = _to_np(grid).copy()
    H, W = arr.shape

    if axis == "V":
        left = arr[:, : W // 2].copy()
        right = arr[:, W - W // 2 :].copy()
        left_filled = np.where(left != background, left, np.fliplr(right))
        right_filled = np.where(right != background, right, np.fliplr(left_filled))
        arr[:, : W // 2] = left_filled
        arr[:, W - W // 2 :] = right_filled
    else:  # "H"
        top = arr[: H // 2, :].copy()
        bottom = arr[H - H // 2 :, :].copy()
        top_filled = np.where(top != background, top, np.flipud(bottom))
        bottom_filled = np.where(bottom != background, bottom, np.flipud(top_filled))
        arr[: H // 2, :] = top_filled
        arr[H - H // 2 :, :] = bottom_filled

    return _to_list(arr)


def count_color(grid: Grid, *, color: int) -> int:
    """Count occurrences of a color (utility, not a grid→grid transform)."""
    return int((_to_np(grid) == color).sum())


def hollow(grid: Grid, *, background: int = 0) -> Grid:
    """Replace interior (non-border) non-background cells with *background*."""
    arr = _to_np(grid).copy()
    H, W = arr.shape
    if H < 3 or W < 3:
        return _to_list(arr)
    interior = arr[1:-1, 1:-1].copy()
    interior[:] = background
    arr[1:-1, 1:-1] = interior
    return _to_list(arr)


def outline(grid: Grid, *, color: int = 1, background: int = 0) -> Grid:
    """Draw a 1-cell border of *color* around all objects."""
    arr = _to_np(grid).copy()
    H, W = arr.shape
    non_bg = arr != background
    # Expand mask by 1 in all directions
    from scipy.ndimage import binary_dilation  # type: ignore[import]
    struct = np.ones((3, 3), dtype=bool)
    expanded = binary_dilation(non_bg, structure=struct)
    border = expanded & ~non_bg
    arr[border] = color
    return _to_list(arr)


def sort_rows_by_color(grid: Grid, *, reference_color: int = 1, background: int = 0) -> Grid:
    """
    Sort rows so that rows containing *reference_color* come first.
    """
    arr = _to_np(grid)
    contains = np.any(arr == reference_color, axis=1)
    order = np.concatenate([np.where(contains)[0], np.where(~contains)[0]])
    return _to_list(arr[order, :])


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

class DSLRegistry:
    """
    Central catalogue of all DSL primitives.

    Each entry stores the callable plus a description of its parameters
    so the synthesiser can enumerate argument combinations.
    """

    def __init__(self) -> None:
        # name -> (callable, default_kwargs_dict)
        self._registry: Dict[str, Tuple[DSLFunction, Dict[str, Any]]] = {}
        self._register_defaults()

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def register(
        self,
        name: str,
        fn: DSLFunction,
        default_kwargs: Optional[Dict[str, Any]] = None,
    ) -> None:
        self._registry[name] = (fn, default_kwargs or {})

    def _register_defaults(self) -> None:
        self.register("identity", identity)
        self.register("rotate_90", rotate_90)
        self.register("rotate_180", rotate_180)
        self.register("rotate_270", rotate_270)
        self.register("flip_horizontal", flip_horizontal)
        self.register("flip_vertical", flip_vertical)
        self.register("flip_diagonal", flip_diagonal)
        self.register("flip_anti_diagonal", flip_anti_diagonal)
        self.register("crop_to_content", crop_to_content, {"background": 0})
        self.register("upscale_2x", upscale, {"factor": 2})
        self.register("upscale_3x", upscale, {"factor": 3})
        self.register("tile_2x2", tile, {"rows": 2, "cols": 2})
        self.register("gravity_down", gravity, {"direction": "down", "background": 0})
        self.register("gravity_up", gravity, {"direction": "up", "background": 0})
        self.register("gravity_left", gravity, {"direction": "left", "background": 0})
        self.register("gravity_right", gravity, {"direction": "right", "background": 0})
        self.register("mirror_complete_V", mirror_complete, {"axis": "V", "background": 0})
        self.register("mirror_complete_H", mirror_complete, {"axis": "H", "background": 0})
        self.register("hollow", hollow, {"background": 0})

    # ------------------------------------------------------------------
    # Lookup / enumeration
    # ------------------------------------------------------------------

    def get(self, name: str) -> Tuple[DSLFunction, Dict[str, Any]]:
        if name not in self._registry:
            raise KeyError(f"DSL primitive '{name}' is not registered.")
        return self._registry[name]

    def apply(self, name: str, grid: Grid, **override_kwargs: Any) -> Grid:
        """Apply a named primitive to a grid, optionally overriding defaults."""
        fn, defaults = self.get(name)
        kwargs = {**defaults, **override_kwargs}
        return fn(grid, **kwargs)

    def names(self) -> List[str]:
        """Return all registered primitive names."""
        return list(self._registry.keys())

    def __len__(self) -> int:
        return len(self._registry)
