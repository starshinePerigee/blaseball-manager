import pytest

from blaseball.util import geometry
from blaseball.stats import lineup


@pytest.fixture(scope='class')
def zero_point():
    return geometry.Coord(0, 0)



class TestCoord:
    def test_zero(self, zero_point):
        assert zero_point.x == 0
        assert zero_point.y == 0
        assert not zero_point
        assert isinstance(str(zero_point), str)  # just make sure this doesn't throw an error

    def test_xy(self, zero_point):
        xy_point = geometry.Coord(3, 4)
        assert zero_point.distance(xy_point) == pytest.approx(5)
        assert xy_point.theta() == pytest.approx(54, abs=1)

    def test_theta(self, zero_point):
        theta_point = geometry.Coord(9, 30, True)
        assert zero_point.distance(theta_point) == pytest.approx(9)


class TestStadiumGeo:
    def test_stadium_size(self, stadium_a):
        assert stadium_a.polygon.area == pytest.approx(110481, abs=10)
        assert stadium_a.polygon.length == pytest.approx(1291, abs=1)

    def test_stadium_contains(self, stadium_a):
        assert not stadium_a.polygon.contains(geometry.Coord(550, 200))
        assert not stadium_a.polygon.contains(geometry.Coord(360, 100))
        assert stadium_a.polygon.contains(geometry.Coord(100, 100))


class TestDefenseGeo:
    # these tests are far from comprehensive.
    def test_place_basepeep(self, stadium_a):
        assert lineup.place_basepeep(0, 3).theta() < 30
        assert 80 < lineup.place_basepeep(2, 3).theta() < 90
        assert lineup.place_basepeep(5, 7).theta() < lineup.place_basepeep(6, 7).theta()
        assert stadium_a.FIRST_BASE.distance(lineup.place_basepeep(0, 3)) < 20
        assert stadium_a.THIRD_BASE.distance(lineup.place_basepeep(2, 3)) < 20

    def test_place_fielder(self):
        rf = lineup.place_fielder(0, 3).theta()
        assert rf < 30
        lf = lineup.place_fielder(2, 3).theta()
        assert 60 < lf < 90
        assert rf + lf == pytest.approx(90, abs=5)
        assert lineup.place_fielder(5, 7).theta() < lineup.place_fielder(6, 7).theta()

    def test_defense_locations(self, defense_1, zero_point):
        catcher_loc = defense_1['catcher'].location
        assert (catcher_loc.x, catcher_loc.y) == (0, 0)
        first_base = defense_1['basepeep 1'].location
        second_base = defense_1['basepeep 2'].location
        shortstop = defense_1['shortstop'].location

        assert first_base.theta() < second_base.theta()
        assert first_base.y < second_base.y
        assert shortstop.theta() > second_base.theta()

        center_field = defense_1['fielder 2'].location
        assert zero_point.distance(center_field) > zero_point.distance(shortstop)

    @pytest.mark.parametrize(
        "location, nearest",
        [
            ((10, 0, False), ('catcher', 'pitcher', 'basepeep 1')),
            ((400, 600, False), ('fielder 3', 'fielder 2')),
            ((90, 90, True), ('basepeep 3', 'pitcher', 'shortstop'))
        ]
    )
    def test_defense_nearest(self, defense_1, location, nearest):
        landing = geometry.Coord(location[0], location[1], location[2])
        assert defense_1.closest(landing)[0].position == nearest[0]

        running_dist = 0
        all_fielders = defense_1.rank_closest(landing)
        assert len(all_fielders) == 9
        for i, fielder in enumerate(all_fielders):
            assert fielder[0].position == nearest[i]
            assert isinstance(fielder[1], float)
            assert fielder[1] > running_dist
            running_dist = fielder[1]

            if i == len(nearest) - 1:
                break
