"""
Subsystem I: Geometric-Topological Perception (The Seer)
=========================================================

Deconstructs input grids into Core Knowledge primitives:
  - Objectness (connected components by color)
  - Goal-directedness (movement / directional patterns)
  - Numbers / Counting
  - Basic Geometry / Topology
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Dict, FrozenSet, List, Optional, Set, Tuple

import numpy as np

# ---------------------------------------------------------------------------
# Type aliases
# ---------------------------------------------------------------------------
Grid = List[List[int]]
Point = Tuple[int, int]


# ---------------------------------------------------------------------------
# Core data structures
# ---------------------------------------------------------------------------

@dataclass
class ArcObject:
    """A spatially contiguous group of cells sharing the same color."""

    color: int
    cells: FrozenSet[Point]
    bounding_box: Tuple[int, int, int, int]  # (row_min, col_min, row_max, col_max)

    # Derived properties computed lazily
    _shape_matrix: Optional[np.ndarray] = field(default=None, repr=False, compare=False)

    # ------------------------------------------------------------------
    # Construction helpers
    # ------------------------------------------------------------------

    @classmethod
    def from_cells(cls, color: int, cells: Set[Point]) -> "ArcObject":
        frozen = frozenset(cells)
        rows = [r for r, _ in frozen]
        cols = [c for _, c in frozen]
        bbox = (min(rows), min(cols), max(rows), max(cols))
        return cls(color=color, cells=frozen, bounding_box=bbox)

    # ------------------------------------------------------------------
    # Derived properties
    # ------------------------------------------------------------------

    @property
    def size(self) -> int:
        return len(self.cells)

    @property
    def height(self) -> int:
        r0, _, r1, _ = self.bounding_box
        return r1 - r0 + 1

    @property
    def width(self) -> int:
        _, c0, _, c1 = self.bounding_box
        return c1 - c0 + 1

    @property
    def center(self) -> Tuple[float, float]:
        rows = [r for r, _ in self.cells]
        cols = [c for _, c in self.cells]
        return (sum(rows) / len(rows), sum(cols) / len(cols))

    @property
    def is_rectangular(self) -> bool:
        r0, c0, r1, c1 = self.bounding_box
        return len(self.cells) == (r1 - r0 + 1) * (c1 - c0 + 1)

    @property
    def shape_matrix(self) -> np.ndarray:
        """Normalised (origin at top-left) boolean mask of the object."""
        if self._shape_matrix is None:
            r0, c0, r1, c1 = self.bounding_box
            mat = np.zeros((r1 - r0 + 1, c1 - c0 + 1), dtype=bool)
            for r, c in self.cells:
                mat[r - r0, c - c0] = True
            self._shape_matrix = mat
        return self._shape_matrix

    # ------------------------------------------------------------------
    # Symmetry
    # ------------------------------------------------------------------

    def has_horizontal_symmetry(self) -> bool:
        return bool(np.array_equal(self.shape_matrix, self.shape_matrix[::-1, :]))

    def has_vertical_symmetry(self) -> bool:
        return bool(np.array_equal(self.shape_matrix, self.shape_matrix[:, ::-1]))

    def has_diagonal_symmetry(self) -> bool:
        mat = self.shape_matrix
        if mat.shape[0] != mat.shape[1]:
            return False
        return bool(np.array_equal(mat, mat.T))


# ---------------------------------------------------------------------------
# Spatial grammar / scene descriptor
# ---------------------------------------------------------------------------

@dataclass
class SceneDescription:
    """Full description of a grid's perceived structure."""

    grid: np.ndarray
    objects: List[ArcObject]
    color_counts: Dict[int, int]
    background_color: int

    # Topology flags
    has_horizontal_symmetry: bool = False
    has_vertical_symmetry: bool = False
    has_diagonal_symmetry: bool = False

    # Counting
    unique_colors: List[int] = field(default_factory=list)
    object_count: int = 0

    # Movement hints (direction vectors between same-color objects)
    movement_hints: List[Tuple[int, int]] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Main perception engine
# ---------------------------------------------------------------------------

class GridPerception:
    """
    Subsystem I — The Seer.

    Converts a raw ARC grid (list[list[int]]) into a richly annotated
    SceneDescription using a Spatial Grammar.
    """

    BACKGROUND = 0

    def __init__(self, connectivity: int = 4):
        """
        Parameters
        ----------
        connectivity : {4, 8}
            Whether to treat diagonal neighbours as connected (8) or not (4).
        """
        if connectivity not in (4, 8):
            raise ValueError("connectivity must be 4 or 8")
        self.connectivity = connectivity

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def perceive(self, grid: Grid) -> SceneDescription:
        """
        Parse a grid and return a full SceneDescription.

        Parameters
        ----------
        grid : list[list[int]]
            The raw ARC grid (H x W integers 0-9).

        Returns
        -------
        SceneDescription
        """
        arr = np.array(grid, dtype=int)
        background = self._detect_background(arr)
        objects = self._extract_objects(arr, background)
        color_counts = self._count_colors(arr)
        unique_colors = sorted(color_counts.keys())
        movement_hints = self._detect_movement(objects)

        desc = SceneDescription(
            grid=arr,
            objects=objects,
            color_counts=color_counts,
            background_color=background,
            unique_colors=unique_colors,
            object_count=len(objects),
            movement_hints=movement_hints,
        )
        desc.has_horizontal_symmetry = self._check_grid_symmetry(arr, "H")
        desc.has_vertical_symmetry = self._check_grid_symmetry(arr, "V")
        desc.has_diagonal_symmetry = self._check_grid_symmetry(arr, "D")
        return desc

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _detect_background(arr: np.ndarray) -> int:
        """The background is the most frequent color (ties broken by lowest value)."""
        unique, counts = np.unique(arr, return_counts=True)
        max_count = counts.max()
        candidates = unique[counts == max_count]
        return int(candidates.min())

    def _extract_objects(
        self, arr: np.ndarray, background: int
    ) -> List[ArcObject]:
        """BFS-based connected-component extraction (ignores background)."""
        H, W = arr.shape
        visited = np.zeros((H, W), dtype=bool)
        objects: List[ArcObject] = []

        neighbours = self._get_neighbour_deltas()

        for r in range(H):
            for c in range(W):
                color = int(arr[r, c])
                if color == background or visited[r, c]:
                    continue
                # BFS flood fill
                cells: Set[Point] = set()
                q: deque[Point] = deque()
                q.append((r, c))
                visited[r, c] = True
                while q:
                    cr, cc = q.popleft()
                    cells.add((cr, cc))
                    for dr, dc in neighbours:
                        nr, nc = cr + dr, cc + dc
                        if (
                            0 <= nr < H
                            and 0 <= nc < W
                            and not visited[nr, nc]
                            and int(arr[nr, nc]) == color
                        ):
                            visited[nr, nc] = True
                            q.append((nr, nc))
                objects.append(ArcObject.from_cells(color, cells))

        return objects

    def _get_neighbour_deltas(self) -> List[Tuple[int, int]]:
        deltas = [(0, 1), (0, -1), (1, 0), (-1, 0)]
        if self.connectivity == 8:
            deltas += [(1, 1), (1, -1), (-1, 1), (-1, -1)]
        return deltas

    @staticmethod
    def _count_colors(arr: np.ndarray) -> Dict[int, int]:
        unique, counts = np.unique(arr, return_counts=True)
        return {int(u): int(c) for u, c in zip(unique, counts)}

    @staticmethod
    def _detect_movement(objects: List[ArcObject]) -> List[Tuple[int, int]]:
        """
        Look for pairs of same-color objects and record their displacement
        vector as a movement hint.
        """
        from collections import defaultdict

        by_color: Dict[int, List[ArcObject]] = defaultdict(list)
        for obj in objects:
            by_color[obj.color].append(obj)

        hints: List[Tuple[int, int]] = []
        for color, objs in by_color.items():
            if len(objs) == 2:
                c0 = objs[0].center
                c1 = objs[1].center
                dr = c1[0] - c0[0]
                dc = c1[1] - c0[1]
                hints.append((int(round(dr)), int(round(dc))))
        return hints

    @staticmethod
    def _check_grid_symmetry(arr: np.ndarray, axis: str) -> bool:
        if axis == "H":
            return bool(np.array_equal(arr, arr[::-1, :]))
        if axis == "V":
            return bool(np.array_equal(arr, arr[:, ::-1]))
        if axis == "D":
            if arr.shape[0] != arr.shape[1]:
                return False
            return bool(np.array_equal(arr, arr.T))
        return False
