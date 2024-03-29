import pytest

import math
import statistics

from blaseball.playball import liveball, gamestate
from blaseball.stats.stadium import Stadium
from blaseball.util.geometry import Coord
from blaseball.stats import stats as s


class TestLiveBall:
    ball_parameters = {
        # "angle, speed, min_feet, max_feet"
        # remember good hit EV is 80 - 120
        '45 degree line drive': (45, 100, 200, 400),
        '2 degree high power': (2, 100, 20, 100),
        '10 degrees': (10, 50, 40, 100),
        '-10 degree line drive equivalent': (-10, 100, 40, 100)
    }

    @pytest.mark.parametrize(
        "angle, speed, min_feet, max_feet",
        ball_parameters.values(),
        ids=list(ball_parameters.keys())
    )
    def test_distance_absolute(self, angle, speed, min_feet, max_feet):
        ball = liveball.LiveBall(angle, 0, speed)
        assert ball.distance() < ball._theoretical_distance()
        assert ball.ground_location().x == ball.distance()
        assert min_feet < ball.distance() < max_feet

    compare_parameters = {
        # greater_angle, greater_speed, lesser_angle, lesser_speed
        '40 v 45 launch angle': (40, 100, 45, 100),
        '10 v 5 launch angle': (10, 100, 5, 100),
        '90 v 91 EV': (10, 91, 10, 90),
        'negative launch angle': (10, 50, -10, 60),
    }

    @pytest.mark.parametrize(
        "greater_angle, greater_speed, lesser_angle, lesser_speed",
        compare_parameters.values(),
        ids=list(compare_parameters.keys())
    )
    def test_distance_relative(self, greater_angle, greater_speed, lesser_angle, lesser_speed):
        greater = liveball.LiveBall(greater_angle, 0, greater_speed)
        lesser = liveball.LiveBall(lesser_angle, 0, lesser_speed)
        assert greater.distance() > lesser.distance()
        assert greater.ground_location().x > lesser.ground_location().x

    @pytest.mark.parametrize("field_angle", (0, 10, 90, 180))
    def test_field_angle_ground_location(self, field_angle):
        ball = liveball.LiveBall(20, field_angle, 20)
        coords = ball.ground_location()
        distance = ball.distance()
        assert coords.x == pytest.approx(math.cos(math.radians(field_angle)) * distance)
        assert coords.y == pytest.approx(math.sin(math.radians(field_angle)) * distance)

    def test_to_string(self):
        ball = liveball.LiveBall(20, 30, 40)
        assert isinstance(str(ball), str)


class TestHitBall:
    @staticmethod
    def print_launch_angle_array(launch_angles, title) -> None:
        print(
            f"{title:>30}:  "
            f"min {min(launch_angles):<6.1f} "
            f"ten {launch_angles[6]:<6.1f} "
            f"mean {statistics.mean(launch_angles):<6.1f} "
            f"ten {launch_angles[-6]:<6.1f} "
            f"max {max(launch_angles):<6.1f} "
        )

    def test_roll_launch_angle(self, patcher):
        patcher.patch_normal('blaseball.playball.liveball.normal')
        print(" ~Launch Angle~")

        hits_base = [liveball.roll_launch_angle(0, 0) for __ in patcher]
        assert statistics.mean(hits_base) == pytest.approx(liveball.BASE_LAUNCH_ANGLE)
        TestHitBall.print_launch_angle_array(hits_base, "Worst case launch angle")

        hits_plus_one_power = [liveball.roll_launch_angle(0, 1) for __ in patcher]
        target_mean = statistics.mean(hits_base) + liveball.LAUNCH_ANGLE_POWER_FACTOR
        assert statistics.mean(hits_plus_one_power) == pytest.approx(target_mean)
        TestHitBall.print_launch_angle_array(hits_plus_one_power, "Zero quality, one power")

        two_quality_one_power = [liveball.roll_launch_angle(2, 1) for __ in patcher]
        assert statistics.mean(two_quality_one_power) == pytest.approx(statistics.mean(two_quality_one_power))
        TestHitBall.print_launch_angle_array(two_quality_one_power, "Two quality one power")
        for i in range(0, 50):
            assert two_quality_one_power[i] > hits_plus_one_power[i]
            assert two_quality_one_power[-(i+1)] < hits_plus_one_power[-(i+1)]

    def test_roll_field_angle(self, patcher):
        patcher.patch_normal('blaseball.playball.liveball.normal')
        all_angles = [liveball.roll_field_angle(30) for __ in patcher]
        assert 0 < min(all_angles) < 5
        assert 85 < max(all_angles) < 90
        assert all_angles[50] == pytest.approx(30, abs=2)
        valid_angles = [x for x in all_angles if x != 45]
        assert len(valid_angles) > 40
        pull_percent = sum([1 for x in valid_angles if x < 45]) / (len(valid_angles) - 12)  # - 12 to reject outliers.
        assert 0.6 < pull_percent < 0.8
        print(f"pull percent at 30 pull: {pull_percent*100:.2f}% on right side.")

    @staticmethod
    def ev_thirty_distance(exit_velocity) -> float:
        return liveball.LiveBall(30, 0, exit_velocity).distance()

    @staticmethod
    def print_ev_list(exit_velocities, title) -> None:
        distances = [TestHitBall.ev_thirty_distance(x) for x in exit_velocities]
        distances_over_350 = sum([1 for x in distances if x >= 350])
        print(
            f"{title:>30}:    "
            f"min {min(exit_velocities):4.0f} mph "
            f"({min(distances):4.0f} ft)   "
            f"ave {statistics.mean(exit_velocities):4.0f} mph "
            f"({statistics.mean(distances):4.0f} ft)   "
            f"max {max(exit_velocities):4.0f} mph "
            f"({max(distances):4.0f} ft)   "
            f"{distances_over_350:>3.0f}% greater than 350 ft"
        )

    def test_roll_exit_velocity_batter_power(self, patcher):
        patcher.patch_normal('blaseball.playball.liveball.normal')
        print(" ~Exit Velocity Batter Power~")

        exit_velocities = [liveball.roll_exit_velocity(1, 0, 1) for __ in patcher]
        one_power_average_ev = (liveball.MIN_EXIT_VELOCITY_AVERAGE + liveball.MAX_EXIT_VELOCITY_AVERAGE) / 2
        assert statistics.mean(exit_velocities) == pytest.approx(one_power_average_ev, abs=10)
        assert exit_velocities[10] < liveball.MAX_EXIT_VELOCITY_AVERAGE

        exit_velocities_0 = [liveball.roll_exit_velocity(1, 0, 0) for __ in patcher]
        assert statistics.mean(exit_velocities_0) == pytest.approx(liveball.MIN_EXIT_VELOCITY_AVERAGE, abs=10)
        exit_velocities_10 = [liveball.roll_exit_velocity(1, 0, 2) for __ in patcher]
        assert statistics.mean(exit_velocities_10) == pytest.approx(liveball.MAX_EXIT_VELOCITY_AVERAGE, abs=10)

        for zero, five, ten in zip(exit_velocities_0, exit_velocities, exit_velocities_10):
            assert zero <= five <= ten

        for ev_list, power in zip([exit_velocities_0, exit_velocities, exit_velocities_10], [0, 1, 2]):
            TestHitBall.print_ev_list(ev_list, f"{power} hitter power")

    def test_roll_exit_velocity_quality(self, patcher):
        qualities = [0, 0.1, 0.5, 1, 2, 5]
        qualities.sort()
        previous = {
            "min": -1,
            "max": -1,
            "ave": -1
        }
        patcher.patch_normal('blaseball.playball.liveball.normal')
        print(" ~Exit Velocity Quality~")
        for quality in qualities:
            exit_velocities = [liveball.roll_exit_velocity(quality, 0, 1) for __ in patcher]
            TestHitBall.print_ev_list(exit_velocities, f"{quality} hit quality")
            assert min(exit_velocities) > previous['min']
            assert max(exit_velocities) > previous['max']
            assert statistics.mean(exit_velocities) > previous['ave']

    def test_exit_velocity_reduction(self, patcher):
        print(" ~Exit Velocity Reduction")
        patcher.patch_normal('blaseball.playball.liveball.normal')
        reduction_evs = {}
        reductions = [-1, -0.1, 0, 0.2, 0.5, 1, 3]
        reductions.sort()
        for reduction in reductions:
            reduction_evs[reduction] = [liveball.roll_exit_velocity(1, reduction, 1) for __ in patcher]

        for i in range(0, len(reductions)-1):
            for faster, slower in zip(reduction_evs[reductions[i]], reduction_evs[reductions[i+1]]):
                assert faster >= slower
                assert slower >= 0

        # evs should never go backwards
        for reduction in reductions:
            for ev0, ev1 in zip(reduction_evs[reduction][:-1], reduction_evs[reduction][1:]):
                assert ev0 <= ev1

            TestHitBall.print_ev_list(reduction_evs[reduction], f"{reduction} reduction")

    @pytest.mark.parametrize(
        "field_angle, distance, text",
        [
            (0, 500, "Home run!"),
            (1, 405, "Off the outfield wall!"),
            (45, 200, None)
        ]
    )
    def test_hit_ball_integrated(self, gamestate_1, messenger_1, patcher, field_angle, distance, text):
        patcher.patch("blaseball.playball.liveball.LiveBall.distance",
                      lambda x: distance)
        patcher.patch("blaseball.playball.liveball.roll_field_angle",
                      lambda batter_pull: field_angle)

        hit_ball = liveball.HitBall(gamestate_1, 0, 0, gamestate_1.batter(), messenger_1)
        assert hit_ball.text == text
        assert hit_ball.live.distance() == distance

    def test_hit_ball_stats(self, patcher, gamestate_1, messenger_1):
        # two averaging stats: average hit distance, and average exit velocity.
        # plus "total home runs"
        def distance_iterator(iteration):  # noqa
            return iteration * 100 + 120  # avoid wall strikes

        # iterate from 100 to 1000
        patcher.patch("blaseball.playball.liveball.LiveBall.distance", distance_iterator, iterations=10)

        def exit_velocity_iterator(quality, reduction, batter_power, iteration):
            return iteration * 10 + 10

        # iterate from 10 to 100
        patcher.patch("blaseball.playball.liveball.roll_exit_velocity", exit_velocity_iterator, iterations=10)

        # fix field angle to be constant down the middle
        patcher.patch("blaseball.playball.liveball.roll_field_angle", lambda batter_pull: 45)

        # fix launch angle to avoid ground rebounds
        patcher.patch("blaseball.playball.liveball.roll_launch_angle", lambda quality, batter_power: 20)

        # stop incrementing batters
        patcher.patch("blaseball.playball.ballgame.BallGame.increment_batter", lambda: None)

        batter = gamestate_1.batter()

        for i, __ in enumerate(patcher):
            ball = liveball.HitBall(gamestate_1, 0, 0, batter, messenger_1)

        assert batter[s.total_hits] == 100
        assert batter[s.average_hit_distance] == pytest.approx(570)
        assert batter[s.average_exit_velocity] == pytest.approx(55)
        assert batter[s.total_home_runs] == 70
