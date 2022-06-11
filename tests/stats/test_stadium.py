import pytest

from blaseball.util import geometry
from blaseball.stats import stadium


class TestStadiumGeo:
    def test_stadium_size(self, stadium_a):
        assert stadium_a.polygon.area == pytest.approx(110481, abs=10)
        assert stadium_a.polygon.length == pytest.approx(1291, abs=1)

    def test_stadium_contains(self, stadium_a):
        assert not stadium_a.polygon.contains(geometry.Coord(550, 200))
        assert not stadium_a.polygon.contains(geometry.Coord(360, 100))
        assert stadium_a.polygon.contains(geometry.Coord(100, 100))


class TestStadium:
    @pytest.mark.parametrize(
        "x_coord, y_coord, is_home_run, is_wall",
        [
            (1, 1, False, False),
            (405, 1, False, True),
            (1, 350, True, False),
            (415, 1, True, False),
            (395, 1, False, False),
            (90, 90, False, False),
        ]
    )
    def test_check_home_run(self, stadium_cut_lf, x_coord, y_coord, is_home_run, is_wall):
        # build a stadium that's a pentagon, basically a right angle square with the corner past third base cut out

        coords = geometry.Coord(x_coord, y_coord)
        home_run, wall = stadium_cut_lf.check_home_run(coords)
        assert home_run == is_home_run
        assert wall == is_wall