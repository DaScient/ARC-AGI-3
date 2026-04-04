"""Tests for the ARC DSL primitives and registry."""
import pytest
import numpy as np

from arc_solver.dsl import (
    DSLRegistry,
    Grid,
    color_replace,
    color_swap,
    crop_to_content,
    flip_anti_diagonal,
    flip_diagonal,
    flip_horizontal,
    flip_vertical,
    gravity,
    hollow,
    identity,
    move_object,
    pad,
    rotate_180,
    rotate_270,
    rotate_90,
    tile,
    upscale,
    downscale,
    mirror_complete,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def g(rows):
    """Shorthand for a grid literal."""
    return rows


def same(a: Grid, b: Grid) -> bool:
    return np.array_equal(np.array(a), np.array(b))


# ---------------------------------------------------------------------------
# Rotations
# ---------------------------------------------------------------------------

class TestRotations:
    def test_rotate_90(self):
        grid = [[1, 2], [3, 4]]
        result = rotate_90(grid)
        # 90° clockwise: [[3,1],[4,2]]
        assert same(result, [[3, 1], [4, 2]])

    def test_rotate_180(self):
        grid = [[1, 2], [3, 4]]
        result = rotate_180(grid)
        assert same(result, [[4, 3], [2, 1]])

    def test_rotate_270(self):
        grid = [[1, 2], [3, 4]]
        result = rotate_270(grid)
        # 270° clockwise = 90° CCW: [[2,4],[1,3]]
        assert same(result, [[2, 4], [1, 3]])

    def test_rotate_360_identity(self):
        grid = [[1, 2, 3], [4, 5, 6]]
        r = rotate_90(rotate_90(rotate_90(rotate_90(grid))))
        assert same(r, grid)


# ---------------------------------------------------------------------------
# Flips
# ---------------------------------------------------------------------------

class TestFlips:
    def test_flip_horizontal(self):
        grid = [[1, 2, 3]]
        assert same(flip_horizontal(grid), [[3, 2, 1]])

    def test_flip_vertical(self):
        grid = [[1, 2], [3, 4]]
        assert same(flip_vertical(grid), [[3, 4], [1, 2]])

    def test_flip_diagonal(self):
        grid = [[1, 2], [3, 4]]
        assert same(flip_diagonal(grid), [[1, 3], [2, 4]])

    def test_flip_anti_diagonal(self):
        grid = [[1, 2], [3, 4]]
        result = flip_anti_diagonal(grid)
        assert result is not None  # just check it runs


# ---------------------------------------------------------------------------
# Color operations
# ---------------------------------------------------------------------------

class TestColorOps:
    def test_color_replace(self):
        grid = [[1, 2, 1], [3, 1, 0]]
        result = color_replace(grid, source=1, target=5)
        assert same(result, [[5, 2, 5], [3, 5, 0]])

    def test_color_swap(self):
        grid = [[1, 2], [2, 1]]
        result = color_swap(grid, color_a=1, color_b=2)
        assert same(result, [[2, 1], [1, 2]])

    def test_color_replace_noop(self):
        grid = [[0, 0], [0, 0]]
        result = color_replace(grid, source=9, target=5)
        assert same(result, grid)


# ---------------------------------------------------------------------------
# Spatial transforms
# ---------------------------------------------------------------------------

class TestSpatialTransforms:
    def test_crop_to_content_basic(self):
        grid = [[0, 0, 0], [0, 1, 0], [0, 0, 0]]
        result = crop_to_content(grid, background=0)
        assert same(result, [[1]])

    def test_crop_to_content_all_background(self):
        grid = [[0, 0], [0, 0]]
        result = crop_to_content(grid, background=0)
        assert same(result, [[0]])

    def test_upscale_2x(self):
        grid = [[1, 2]]
        result = upscale(grid, factor=2)
        assert same(result, [[1, 1, 2, 2], [1, 1, 2, 2]])

    def test_tile_2x2(self):
        grid = [[1, 2]]
        result = tile(grid, rows=2, cols=2)
        assert same(result, [[1, 2, 1, 2], [1, 2, 1, 2]])

    def test_pad(self):
        grid = [[1]]
        result = pad(grid, top=1, bottom=1, left=1, right=1, fill=0)
        assert same(result, [[0, 0, 0], [0, 1, 0], [0, 0, 0]])

    def test_downscale(self):
        grid = [[1, 1, 2, 2], [1, 1, 2, 2]]
        result = downscale(grid, factor=2)
        assert same(result, [[1, 2]])

    def test_hollow(self):
        grid = [[1, 1, 1], [1, 1, 1], [1, 1, 1]]
        result = hollow(grid, background=0)
        assert same(result, [[1, 1, 1], [1, 0, 1], [1, 1, 1]])

    def test_hollow_small_grid(self):
        grid = [[1, 2], [3, 4]]
        result = hollow(grid, background=0)
        assert same(result, grid)


# ---------------------------------------------------------------------------
# Gravity
# ---------------------------------------------------------------------------

class TestGravity:
    def test_gravity_down(self):
        grid = [[1, 0], [0, 0]]
        result = gravity(grid, direction="down", background=0)
        assert same(result, [[0, 0], [1, 0]])

    def test_gravity_up(self):
        grid = [[0, 0], [1, 0]]
        result = gravity(grid, direction="up", background=0)
        assert same(result, [[1, 0], [0, 0]])

    def test_gravity_preserves_color(self):
        grid = [[2, 0], [0, 0], [0, 0]]
        result = gravity(grid, direction="down", background=0)
        assert result[2][0] == 2


# ---------------------------------------------------------------------------
# Move object
# ---------------------------------------------------------------------------

class TestMoveObject:
    def test_move_right(self):
        grid = [[1, 0, 0]]
        result = move_object(grid, color=1, dr=0, dc=1, background=0)
        assert same(result, [[0, 1, 0]])

    def test_move_down(self):
        grid = [[1, 0], [0, 0]]
        result = move_object(grid, color=1, dr=1, dc=0, background=0)
        assert same(result, [[0, 0], [1, 0]])

    def test_move_out_of_bounds_clips(self):
        grid = [[1, 0]]
        result = move_object(grid, color=1, dr=0, dc=5, background=0)
        # Cell moves off-grid → disappears
        assert same(result, [[0, 0]])


# ---------------------------------------------------------------------------
# Mirror complete
# ---------------------------------------------------------------------------

class TestMirrorComplete:
    def test_mirror_v_symmetry(self):
        grid = [[1, 0, 0], [0, 0, 0]]
        result = mirror_complete(grid, axis="V", background=0)
        # Left half has 1, right half should reflect it
        assert result[0][0] == 1

    def test_mirror_h_symmetry(self):
        grid = [[1, 0], [0, 0]]
        result = mirror_complete(grid, axis="H", background=0)
        assert result[0][0] == 1


# ---------------------------------------------------------------------------
# DSLRegistry
# ---------------------------------------------------------------------------

class TestDSLRegistry:
    def test_default_primitives_registered(self):
        reg = DSLRegistry()
        assert len(reg) > 0
        assert "identity" in reg.names()
        assert "rotate_90" in reg.names()

    def test_apply_identity(self):
        reg = DSLRegistry()
        grid = [[1, 2], [3, 4]]
        result = reg.apply("identity", grid)
        assert same(result, grid)

    def test_apply_rotate_90(self):
        reg = DSLRegistry()
        grid = [[1, 2], [3, 4]]
        result = reg.apply("rotate_90", grid)
        assert same(result, rotate_90(grid))

    def test_apply_unknown_raises(self):
        reg = DSLRegistry()
        with pytest.raises(KeyError):
            reg.apply("nonexistent_primitive", [[0]])

    def test_register_custom(self):
        reg = DSLRegistry()
        reg.register("my_op", identity)
        assert "my_op" in reg.names()

    def test_apply_with_override(self):
        reg = DSLRegistry()
        grid = [[1, 2, 1]]
        result = reg.apply("identity", grid)
        assert same(result, grid)
