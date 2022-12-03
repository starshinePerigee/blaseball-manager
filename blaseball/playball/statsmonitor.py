"""Stats monitor is a class which subscribes to a game feed, and updates player stats accordingly."""

from blaseball.util.messenger import Messenger
from blaseball.playball.gamestate import GameState, GameTags
from blaseball.playball import hitting, pitching
from blaseball.stats import stats as s


class StatsMonitor:
    """A listener class which updates player stats based game events. This class is created by ballgame, as it
    stores the last game state for reference purposes."""
    def __init__(self, messenger: Messenger, starting_state: GameState):
        self.current_state = starting_state

        self.subscribe_all(messenger)

    def subscribe_all(self, messenger):
        """Subscribe all relevant functions to the specific messenger feed."""

        # use negative priority in case things affect the pitch (they should be recorded by the stats)
        messenger.subscribe(self.new_game_state, GameTags.pre_tick, priority=-10)
        messenger.subscribe(self.update_pitch, GameTags.pitch, priority=-10)
        messenger.subscribe(self.update_swing, GameTags.swing, priority=-10)

    def new_game_state(self, game_state: GameState):
        self.current_state = game_state

    def update_pitch(self, pitch: pitching.Pitch):
        catcher = self.current_state.defense()['catcher']
        catcher[s.pitches_called] += 1
        catcher[s.total_called_location] += pitch.target

        pitcher = self.current_state.defense()['pitcher']
        pitcher[s.pitches_thrown] += 1
        pitcher[s.total_pitch_difficulty] += pitch.difficulty
        pitcher[s.total_pitch_obscurity] += pitch.obscurity
        pitcher[s.average_pitch_distance_from_edge] += min(abs(pitch.location - 1), abs(pitch.location + 1))
        pitcher[s.average_pitch_distance_from_call] += abs(pitch.location - pitch.target)
        pitcher[s.total_reduction] += pitch.reduction

    def update_swing(self, swing: hitting.Swing):
        batter = self.current_state.batter()
        batter[s.pitches_seen] += 1
        batter[s.total_strikes] += float(swing.strike)
        batter[s.total_fouls] += float(swing.foul)
        batter[s.total_hits] += float(swing.hit)
        batter[s.total_pitch_read_percent] += swing.read_chance


"""
    state_ticks = 'state ticks <GameState>'
    new_batter = 'new player up to bat <Player>'
    new_inning = 'new inning reached <int>'
    new_half = 'new inning half reached <int>'
    game_over = 'game is complete <Update>'
    game_start = 'first message of a new game. <Update>'

    game_updates = 'game updates <Update>'
    pitch = 'pitch was thrown <Pitch>'
    swing = 'swing was swung <Swing>'
    hit_ball = 'ball is hit <HitBall>'
    bases_update = 'basepath update <BaseSummary>'
    player_walked = 'player walked to first <Player>'
    home_run = 'home run was hit <int>'
    cycle_batting_order = 'every batter hit <Lineup>'
    runs_scored = 'runs were scored <int/Decimal>'
    strike = 'strike was thrown <bool: strike swinging?>'
    ball = 'ball was thrown <None>'
    foul = 'foul was hit <None>'
    outs = 'players out for any cause <int>'

"""