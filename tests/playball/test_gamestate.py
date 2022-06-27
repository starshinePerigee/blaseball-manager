from blaseball.playball.gamestate import GameState, GameRules, BaseSummary
from blaseball.stats.lineup import Lineup


class TestBaseSummary:
    def test_init_empty(self, player_1):
        summary = BaseSummary(total_bases=4)
        assert len(summary) == 0
        assert summary[4] is None

        summary[1] = player_1
        assert summary[1] == player_1

    def test_init_basepaths(self, empty_basepaths, batters_4):
        empty_basepaths[3] = batters_4[3]
        empty_basepaths[2] = batters_4[2]
        empty_basepaths[1] = batters_4[1]

        summary = BaseSummary(basepaths=empty_basepaths)
        assert len(summary) == 3
        for i in range(1, 4):
            assert summary[i] == batters_4[i]

        del(summary[2])
        assert len(summary) == 2
        assert summary[2] is None

    def test_init_from_full_basepaths(self, empty_basepaths, batters_4):
        for i in range(1, 4):
            empty_basepaths[i] = batters_4[i]
        summary = BaseSummary(basepaths=empty_basepaths)

        assert summary.bases[1:] == batters_4[1:]

    def test_enumerate(self, batters_4):
        summary = BaseSummary(total_bases=4) # 5 including home
        for i, batter in enumerate(batters_4):
            summary[i+1] = batter

        for i, base in enumerate(summary[1:5]):
            assert base == batters_4[i]

    def test_strings(self, batters_4):
        summary = BaseSummary(3)
        for i in range(3):
            summary[i] = batters_4[i]

        assert isinstance(str(summary), str)
        assert isinstance(repr(summary), str)


class TestGameState:
    def test_offense_defense(self, league_2, stadium_a):
        home = league_2[0]
        home_lineup = Lineup("Home Lineup")
        home_lineup.generate(home, in_order=True)
        away = league_2[1]
        away_lineup = Lineup("Away Lineup")
        away_lineup.generate(away, in_order=True)

        state = GameState(home_lineup, away_lineup, stadium_a, GameRules())

        assert state.offense() is away_lineup
        assert state.defense() is home_lineup

        state.inning_half = 0

        assert state.offense() is home_lineup
        assert state.defense() is away_lineup

    def test_batter(self, gamestate_1):
        home_lineup = gamestate_1.home_team
        away_lineup = gamestate_1.away_team

        assert gamestate_1.batter() == away_lineup['batter 1']
        assert gamestate_1.batter(1) == away_lineup['batter 2']

        gamestate_1.inning_half = 0
        gamestate_1.at_bat_numbers[gamestate_1.offense_i()] = 6

        assert gamestate_1.batter() == home_lineup['batter 7']
        assert gamestate_1.batter(2) == home_lineup['batter 9']
        assert gamestate_1.batter(4) == home_lineup['batter 2']

    def test_boolean_base_list(self, gamestate_1, batters_4):
        assert gamestate_1.boolean_base_list() == [False, False, False]
        gamestate_1.bases[1] = batters_4[1]
        assert gamestate_1.boolean_base_list() == [True, False, False]
        gamestate_1.bases[3] = batters_4[3]
        assert gamestate_1.boolean_base_list() == [True, False, True]