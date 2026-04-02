"""Tests for Subsystem I: Geometric-Topological Perception."""
import pytest
import numpy as np

from arc_solver.perception import GridPerception, ArcObject, SceneDescription


@pytest.fixture
def perceiver():
    return GridPerception()


# ---------------------------------------------------------------------------
# ArcObject
# ---------------------------------------------------------------------------

class TestArcObject:
    def test_from_cells_basic(self):
        obj = ArcObject.from_cells(color=1, cells={(0, 0), (0, 1), (1, 0)})
        assert obj.color == 1
        assert obj.size == 3
        assert obj.bounding_box == (0, 0, 1, 1)

    def test_width_height(self):
        obj = ArcObject.from_cells(color=2, cells={(1, 2), (1, 3), (2, 2), (2, 3)})
        assert obj.width == 2
        assert obj.height == 2

    def test_is_rectangular_true(self):
        obj = ArcObject.from_cells(color=1, cells={(0, 0), (0, 1), (1, 0), (1, 1)})
        assert obj.is_rectangular is True

    def test_is_rectangular_false(self):
        obj = ArcObject.from_cells(color=1, cells={(0, 0), (0, 1), (1, 0)})
        assert obj.is_rectangular is False

    def test_center(self):
        obj = ArcObject.from_cells(color=3, cells={(0, 0), (2, 2)})
        assert obj.center == (1.0, 1.0)

    def test_shape_matrix(self):
        obj = ArcObject.from_cells(color=1, cells={(0, 0), (0, 1)})
        mat = obj.shape_matrix
        assert mat.shape == (1, 2)
        assert mat[0, 0] is np.bool_(True)
        assert mat[0, 1] is np.bool_(True)

    def test_horizontal_symmetry(self):
        # 2x2 square — symmetric in all axes
        obj = ArcObject.from_cells(color=1, cells={(0, 0), (0, 1), (1, 0), (1, 1)})
        assert obj.has_horizontal_symmetry() is True

    def test_vertical_symmetry(self):
        obj = ArcObject.from_cells(color=1, cells={(0, 0), (0, 1), (1, 0), (1, 1)})
        assert obj.has_vertical_symmetry() is True

    def test_diagonal_symmetry(self):
        obj = ArcObject.from_cells(color=1, cells={(0, 0), (0, 1), (1, 0), (1, 1)})
        assert obj.has_diagonal_symmetry() is True


# ---------------------------------------------------------------------------
# GridPerception
# ---------------------------------------------------------------------------

class TestGridPerception:
    def test_perceive_returns_scene(self, perceiver):
        grid = [[0, 0, 0], [0, 1, 0], [0, 0, 0]]
        scene = perceiver.perceive(grid)
        assert isinstance(scene, SceneDescription)

    def test_background_detection_most_frequent(self, perceiver):
        grid = [[0, 0, 1], [0, 1, 0], [1, 0, 0]]
        scene = perceiver.perceive(grid)
        assert scene.background_color == 0

    def test_object_extraction_single_object(self, perceiver):
        grid = [[0, 0, 0], [0, 1, 0], [0, 0, 0]]
        scene = perceiver.perceive(grid)
        assert scene.object_count == 1
        assert scene.objects[0].color == 1
        assert scene.objects[0].size == 1

    def test_object_extraction_two_objects(self, perceiver):
        grid = [[1, 0, 2], [0, 0, 0], [0, 0, 0]]
        scene = perceiver.perceive(grid)
        assert scene.object_count == 2
        colors = {o.color for o in scene.objects}
        assert colors == {1, 2}

    def test_object_extraction_connected_object(self, perceiver):
        grid = [[1, 1, 0], [1, 0, 0], [0, 0, 0]]
        scene = perceiver.perceive(grid)
        assert scene.object_count == 1
        assert scene.objects[0].size == 3

    def test_color_counts(self, perceiver):
        grid = [[1, 1, 2], [0, 0, 0]]
        scene = perceiver.perceive(grid)
        assert scene.color_counts[1] == 2
        assert scene.color_counts[2] == 1

    def test_unique_colors(self, perceiver):
        grid = [[1, 2, 3], [0, 0, 0]]
        scene = perceiver.perceive(grid)
        assert 1 in scene.unique_colors
        assert 2 in scene.unique_colors

    def test_horizontal_symmetry_detected(self, perceiver):
        grid = [[1, 0, 0], [0, 0, 0], [1, 0, 0]]
        scene = perceiver.perceive(grid)
        assert scene.has_horizontal_symmetry is True

    def test_vertical_symmetry_detected(self, perceiver):
        grid = [[1, 0, 1], [0, 0, 0], [0, 0, 0]]
        scene = perceiver.perceive(grid)
        assert scene.has_vertical_symmetry is True

    def test_no_symmetry(self, perceiver):
        grid = [[1, 0, 0], [0, 0, 0], [0, 0, 2]]
        scene = perceiver.perceive(grid)
        assert scene.has_horizontal_symmetry is False
        assert scene.has_vertical_symmetry is False

    def test_movement_hints(self, perceiver):
        # Two objects of the same color horizontally displaced
        grid = [[1, 0, 0, 0, 1], [0, 0, 0, 0, 0]]
        scene = perceiver.perceive(grid)
        assert len(scene.movement_hints) == 1

    def test_connectivity_8(self):
        perceiver8 = GridPerception(connectivity=8)
        # Diagonal connection
        grid = [[1, 0], [0, 1]]
        scene = perceiver8.perceive(grid)
        # With 8-connectivity the two diagonal cells form one object
        assert scene.object_count == 1

    def test_connectivity_4(self, perceiver):
        # Same grid — 4-connectivity gives two objects
        grid = [[1, 0], [0, 1]]
        scene = perceiver.perceive(grid)
        assert scene.object_count == 2

    def test_invalid_connectivity(self):
        with pytest.raises(ValueError):
            GridPerception(connectivity=6)

    def test_empty_background(self, perceiver):
        grid = [[0, 0], [0, 0]]
        scene = perceiver.perceive(grid)
        assert scene.object_count == 0

    def test_grid_numpy_representation(self, perceiver):
        grid = [[1, 2], [3, 4]]
        scene = perceiver.perceive(grid)
        assert scene.grid.shape == (2, 2)
        assert int(scene.grid[0, 0]) == 1
