import pytest

from blaseball.playball.statsmonitor import StatsMonitor
from blaseball.playball.gamestate import GameState
from blaseball.playball.hitting import Swing
from blaseball.stats import stats as s


class TestStatsMonitor:
    def test_stats_init(self, ballgame_1):
        stats_monitor = StatsMonitor(ballgame_1.messenger, ballgame_1.state)
        assert stats_monitor.current_state is ballgame_1.state

    def test_new_game_state(self, stats_monitor_1, gamestate_1):
        new_state = GameState(gamestate_1.home_team, gamestate_1.away_team, gamestate_1.stadium, gamestate_1.rules)
        new_state.outs = 2

        stats_monitor_1.new_game_state(new_state)

        assert stats_monitor_1.current_state is new_state
        assert stats_monitor_1.current_state.outs == 2

    def test_update_pitch(self, stats_monitor_1, pitch_1, gamestate_1):
        pitcher = gamestate_1.defense()['pitcher']
        catcher = gamestate_1.defense()['catcher']

        stats_monitor_1.update_pitch(pitch_1)

        assert catcher[s.pitches_called] == 1
        assert pitcher[s.pitches_thrown] == 1
        assert pitcher[s.average_pitch_difficulty] == pitch_1.difficulty
        assert pitcher[s.thrown_strike_rate] == pytest.approx(1)

        stats_monitor_1.update_pitch(pitch_1)

        assert catcher[s.pitches_called] == 2
        assert pitcher[s.pitches_thrown] == 2
        assert pitcher[s.average_pitch_difficulty] == pitch_1.difficulty
        assert pitcher[s.thrown_strike_rate] == pytest.approx(1)

    def test_update_hit(self, stats_monitor_1, pitch_1, gamestate_1, patcher):
        patcher.patch('blaseball.playball.hitting.roll_for_swing_decision', lambda swing_chance: True)
        patcher.patch('blaseball.playball.hitting.roll_hit_quality', lambda net_contact: 2)
        batter = gamestate_1.batter()
        swing = Swing(gamestate_1, pitch_1, batter)

        stats_monitor_1.update_swing(swing)

        assert batter[s.pitches_seen] == 1
        assert batter[s.strike_rate] == pytest.approx(0)


class TestStatsMonitorIntegrated:
    def test_state_update_state(self, ballgame_1, stats_monitor_1, patcher):
        ballgame_1.state.outs = 2
        ballgame_1.state.strikes = 1
        patcher.patch('blaseball.playball.ballgame.BallGame.start_at_bat', lambda self: None)
        ballgame_1.send_tick()

        assert stats_monitor_1.current_state.outs == 2
        assert stats_monitor_1.current_state.strikes == 1
