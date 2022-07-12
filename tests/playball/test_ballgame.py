import pytest

from blaseball.playball.gamestate import GameState, GameTags

from decimal import Decimal


class TestBallGame:

    def test_score_runs(self, ballgame_1, count_store_all, messenger_1):
        ballgame_1.score_runs(2)
        assert ": 0 -" in count_store_all[0].text
        assert count_store_all[0].text[-3:] == ": 2"
        ballgame_1.state.inning_half = 0
        ballgame_1.score_runs(3)
        assert ": 3 -" in count_store_all[0].text
        assert count_store_all[0].text[-3:] == ": 2"

    def test_add_ball(self, ballgame_1, pitch_manager_1, count_store_all):
        ballgame_1.add_ball()
        assert ballgame_1.state.balls == 1
        assert "1 - 0" in count_store_all[0].text
        ballgame_1.state.balls = 3
        ballgame_1.add_ball()
        assert ballgame_1.state.bases[1] == ballgame_1.state.offense()['batter 1']
        assert ballgame_1.state.balls == 4
        assert ballgame_1.state.at_bat_numbers == [0, 1]
        assert ballgame_1.needs_new_batter[ballgame_1.state.offense_i()]

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

    def test_batter_mercy(self, ballgame_1, count_store_all, pitch_manager_1, patcher):
        # guarantee no-swing, all strikes
        patcher.patch('blaseball.playball.hitting.roll_for_swing_decision', lambda swing_chance: False)
        patcher.patch('blaseball.playball.pitching.roll_location', lambda target_location, pitcher_accuracy: 0.0)
        ballgame_1.send_tick()
        ballgame_1.batter_mercy_count = 63
        ballgame_1.send_tick()
        assert ballgame_1.state.scores[ballgame_1.state.offense_i()] == Decimal('0.9')
        assert ballgame_1.state.batter() == ballgame_1.state.offense()['batter 2']
        assert ballgame_1.state.outs == 1
        assert count_store_all.tag_inventory()[GameTags.new_batter] == 2

    def test_pitcher_mercy(self, ballgame_1, count_store_all, pitch_manager_1, patcher):
        # guarantee no-swing, all balls
        patcher.patch('blaseball.playball.hitting.roll_for_swing_decision', lambda swing_chance: False)
        patcher.patch('blaseball.playball.pitching.roll_location', lambda target_location, pitcher_accuracy: 2.0)
        ballgame_1.send_tick()
        ballgame_1.pitcher_mercy_count = 63
        ballgame_1.state.balls = 3
        ballgame_1.send_tick()
        assert ballgame_1.state.scores[ballgame_1.state.defense_i()] == Decimal('1.1')
        assert count_store_all.tag_inventory()[GameTags.new_half] == 1

    def test_full_mercy(self, ballgame_1):
        # if something catastrophically fails with pitch_manager (such as not being instantiated),
        # make sure the mercy rules still lead to the end of a ballgame.
        loops = 0
        while ballgame_1.live_game and loops < 100000:
            ballgame_1.send_tick()
            loops += 1
        # you'd think this test is slow but it actually zips without any pitchmanager to simulate
        assert loops < 100000

    def test_send_tick_new_batter(self, ballgame_1, count_store_all):
        ballgame_1.send_tick()
        assert "stepping up" in count_store_all[1].text
        assert ballgame_1.state.offense()['batter 1'] == count_store_all[0].batter()

        ballgame_1.state.increment_batting_order(7)
        assert ballgame_1.state.at_bat_numbers[ballgame_1.state.offense_i()] == 7

        ballgame_1.send_tick()
        assert ballgame_1.state.offense()['batter 8'] == count_store_all[0].batter()

    def test_next_batter_after_hit(self, ballgame_1, count_store_all, pitch_manager_1, seed_randoms, patcher):
        # guarantee no-swing
        patcher.patch('blaseball.playball.hitting.roll_for_swing_decision', lambda swing_chance: False)
        ballgame_1.send_tick()  # send tick to clear need new batter state
        assert not ballgame_1.needs_new_batter[ballgame_1.state.offense_i()]

        # guarantee hit
        patcher.patch('blaseball.playball.hitting.roll_for_swing_decision', lambda swing_chance: True)
        patcher.patch('blaseball.playball.hitting.roll_hit_quality', lambda net_contact: 4.0)
        patcher.patch('blaseball.stats.stadium.Stadium.check_home_run', lambda self, location: (False, False))  # noqa
        ballgame_1.send_tick()

        assert ballgame_1.needs_new_batter[ballgame_1.state.offense_i()]
        assert count_store_all.tag_inventory()[GameTags.new_batter] == 1

    def test_end_half_inning(self, ballgame_1, count_store_all, pitch_manager_1, seed_randoms, patcher):
        # guarantee no-swing, all strikes
        patcher.patch('blaseball.playball.hitting.roll_for_swing_decision', lambda swing_chance: False)
        patcher.patch('blaseball.playball.pitching.roll_location', lambda target_location, pitcher_accuracy: 0.0)
        ballgame_1.send_tick()  # game start includes a new batter, which resets strikes and outs, so we need a first
        # tick so we can set these later.

        ballgame_1.state.strikes = 2
        ballgame_1.state.outs = 2
        ballgame_1.send_tick()
        ballgame_1.send_tick()

        assert ballgame_1.state.offense() is ballgame_1.state.home_team
        assert ballgame_1.state.batter() == ballgame_1.state.home_team['batter 1']
        assert ballgame_1.state.strikes == 1
        assert ballgame_1.state.outs == 0
        assert ballgame_1.state.inning_half == 0
        assert count_store_all.tag_inventory()[GameTags.new_half] == 1

    def test_end_full_inning(self, ballgame_1, count_store_all, pitch_manager_1, seed_randoms, patcher):
        # guarantee no-swing, all strikes
        patcher.patch('blaseball.playball.hitting.roll_for_swing_decision', lambda swing_chance: False)
        patcher.patch('blaseball.playball.pitching.roll_location', lambda target_location, pitcher_accuracy: 0.0)
        ballgame_1.send_tick()

        # step through a half inning
        ballgame_1.state.strikes = 2
        ballgame_1.state.outs = 2
        ballgame_1.send_tick()
        ballgame_1.send_tick()
        ballgame_1.state.strikes = 2
        ballgame_1.state.outs = 2

        count_store_all.clear()
        ballgame_1.send_tick()
        ballgame_1.send_tick()

        assert ballgame_1.state.offense() is ballgame_1.state.away_team
        assert ballgame_1.state.strikes == 1
        assert ballgame_1.state.outs == 0
        assert ballgame_1.state.inning_half == 1
        assert count_store_all.tag_inventory()[GameTags.new_half] == 1
        assert count_store_all.tag_inventory()[GameTags.new_inning] == 1

