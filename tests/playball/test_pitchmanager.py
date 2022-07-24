from blaseball.playball.pitching import Pitch
from blaseball.playball.hitting import Swing
from blaseball.playball.gamestate import GameTags, BaseSummary
from blaseball.util.messenger import Printer


class TestPitchManager:
    def test_strike(self, patcher, messenger_1, pitch_manager_1, count_store_all, gamestate_1):

        # force strike looking
        patcher.patch('blaseball.playball.pitching.roll_location', lambda target_location, pitcher_accuracy: 0.5)
        patcher.patch('blaseball.playball.hitting.roll_for_swing_decision', lambda swing_chance: False)

        messenger_1.send(gamestate_1, GameTags.state_ticks)

        pitch_hopefully = count_store_all[-2]
        assert isinstance(pitch_hopefully, Pitch)
        assert pitch_hopefully.location == 0.5

        swing_hopefully = count_store_all[-3]
        assert isinstance(swing_hopefully, Swing)
        assert swing_hopefully.strike

    def test_fielded_hit(self, patcher, messenger_1, pitch_manager_1, count_store_all, gamestate_1, batters_4):
        # load the bases
        for i in range(1, 4):
            gamestate_1.bases[i] = batters_4[i]

        # force hit
        patcher.patch('blaseball.playball.hitting.roll_for_swing_decision', lambda swing_chance: True)
        patcher.patch('blaseball.playball.hitting.roll_hit_quality', lambda net_contact: 2)
        patcher.patch("blaseball.playball.liveball.roll_exit_velocity",
                      lambda quality, reduction, batter_power: 80)
        patcher.patch("blaseball.playball.liveball.roll_field_angle", lambda batter_pull: 60)
        patcher.patch("blaseball.playball.liveball.roll_launch_angle", lambda quality, batter_power: 20)

        # force quadruple play?
        patcher.patch("blaseball.playball.fielding.roll_to_catch", lambda odds: True)
        patcher.patch("blaseball.playball.fielding.calc_throw_duration_base", lambda throwing, distance: 0.01)
        patcher.patch("blaseball.playball.fielding.calc_decision_time", lambda grabbiness: 0.01)
        patcher.patch("blaseball.playball.liveball.LiveBall.flight_time", lambda self: 0.01)

        printer = Printer(messenger_1, GameTags.game_updates)  # noqa

        print(" ~Quadruple Play Pitch Manager Test~")
        messenger_1.send(gamestate_1, GameTags.state_ticks)

        # note that since count_store_all is below pitch_manager_1 in the messenger recipent list,
        # all of pitch_manager_1's messages arrive before the game state update tick.

        assert len(count_store_all) > 10
        assert count_store_all[1] == 4  # four outs
        base_summary = count_store_all[0]
        assert isinstance(base_summary, BaseSummary)
        assert base_summary.bases == [None, None, None, None]

    def test_player_walked(self, messenger_1, pitch_manager_1, count_store_all, gamestate_1, batters_4):
        gamestate_1.bases[3] = batters_4[0]
        gamestate_1.bases[1] = batters_4[1]
        messenger_1.send(gamestate_1.bases, GameTags.bases_update)

        messenger_1.send(batters_4[2], GameTags.player_walked)

        assert len(count_store_all) == 3
        summary_hopefully = count_store_all[0]
        assert isinstance(summary_hopefully, BaseSummary)
        assert summary_hopefully[1] == batters_4[2]

        messenger_1.send(batters_4[3], GameTags.player_walked)
        assert count_store_all.tag_inventory()[GameTags.runs_scored] == 1
        assert count_store_all[1] == 1
        summary_hopefully = count_store_all[0]
        assert isinstance(summary_hopefully, BaseSummary)
        assert summary_hopefully[1] == batters_4[3]
