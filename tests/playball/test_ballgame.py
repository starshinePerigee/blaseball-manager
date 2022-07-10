import pytest

from blaseball.playball.gamestate import GameState


class TestBallGame:

    def test_score_runs(self, ballgame_1, count_store_all, messenger_1):
        ballgame_1.score_runs(2)
        assert ": 0 -" in count_store_all[0].text
        assert count_store_all[0].text[-3:] == ": 2"
        ballgame_1.state.inning_half = 0
        ballgame_1.score_runs(3)
        assert ": 3 -" in count_store_all[0].text
        assert count_store_all[0].text[-3:] == ": 2"

    def test_add_ball(self, ballgame_1, count_store_all):
        ballgame_1.add_ball()
        assert ballgame_1.state.balls == 1
        assert "1 - 0" in count_store_all[0].text
        ballgame_1.state.balls = 3
        ballgame_1.add_ball()
        assert ballgame_1.state.balls == 0
        assert ballgame_1.state.bases[0] == ballgame_1.state.offense()['batter 1']
        assert ballgame_1.state.at_bat_numbers == [0, 1]

    def test_add_foul(self, ballgame_1, count_store_all):
        ballgame_1.state.strikes = 1
        ballgame_1.add_foul()
        assert ballgame_1.state.strikes == 2
        assert len(count_store_all) == 1
        assert "Foul ball. 0 - 2" in count_store_all[0].text

        ballgame_1.add_foul()
        assert ballgame_1.state.strikes == 2
        assert len(count_store_all) == 2
        assert "Foul ball. 0 - 2" in count_store_all[0].text

    def test_add_strike(self, ballgame_1, count_store_all):
        ballgame_1.needs_new_batter = [False, False]
        assert ballgame_1.state.strikes == 0
        ballgame_1.add_strike(False)
        assert ballgame_1.state.strikes == 1
        assert "looking. 0 - 1" in count_store_all[0].text
        ballgame_1.add_strike(True)
        assert ballgame_1.state.strikes == 2
        assert "swinging. 0 - 2" in count_store_all[0].text
        ballgame_1.add_strike(True)
        assert ballgame_1.needs_new_batter[1]
        assert ballgame_1.state.at_bat_numbers == [0, 1]
        assert count_store_all[0] == 1
        assert "struck out swinging" in count_store_all[1].text

    def test_send_tick_new_batter(self, ballgame_1, count_store_all):
        ballgame_1.send_tick()
        assert "stepping up" in count_store_all[1].text
        assert ballgame_1.state.offense()['batter 1'] == count_store_all[0].batter()

        ballgame_1.state.increment_batting_order(7)
        assert ballgame_1.state.at_bat_numbers[ballgame_1.state.offense_i()] == 7

        ballgame_1.send_tick()
        assert ballgame_1.state.offense()['batter 8'] == count_store_all[0].batter()

    def test_next_batter_after_hit(self, ballgame_1, pitch_manager_1, count_store_all, seed_randoms, patcher):
        # guarantee no-swing
        patcher.patch('blaseball.playball.hitting.roll_for_swing_decision', lambda swing_chance: False)
        ballgame_1.send_tick()  # send tick to clear need new batter state
        assert not ballgame_1.needs_new_batter[ballgame_1.state.offense_i()]

        # guarantee hit
        patcher.patch('blaseball.playball.hitting.roll_for_swing_decision', lambda swing_chance: True)
        patcher.patch('blaseball.playball.hitting.roll_hit_quality', lambda net_contact: 4.0)
        patcher.patch('blaseball.stats.stadium.Stadium.check_home_run', lambda self, location: (False, False))  # noqa
        ballgame_1.send_tick()

        count_store_all.print_all()
        assert ballgame_1.needs_new_batter[ballgame_1.state.offense_i()]

    def test_end_half_inning(self):
        pass

    def test_end_full_inning(self):
        pass
