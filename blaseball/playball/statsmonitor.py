"""Stats monitor is a class which subscribes to a game feed, and updates player stats accordingly."""

from decimal import Decimal

from blaseball.util.messenger import Messenger
from blaseball.playball.gamestate import GameState, GameTags
from blaseball.playball import hitting, pitching, liveball, fielding
from blaseball.stats import stats as s

from typing import Union


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
        messenger.subscribe(self.update_liveball, GameTags.hit_ball, priority=-10)
        messenger.subscribe(self.update_runs_batted_in, GameTags.runs_scored, priority=-10)

    def new_game_state(self, game_state: GameState):
        self.current_state = game_state

    def update_pitch(self, pitch: pitching.Pitch):
        catcher = self.current_state.defense()['catcher']
        catcher[s.pitches_called] += 1
        catcher[s.total_called_location] += pitch.target

        pitcher = self.current_state.defense()['pitcher']
        pitcher[s.pitches_thrown] += 1
        pitcher[s.total_strikes_thrown] += float(pitch.strike)
        pitcher[s.total_pitch_difficulty] += pitch.difficulty
        pitcher[s.total_pitch_obscurity] += pitch.obscurity
        pitcher[s.total_pitch_distance_from_edge] += min(abs(pitch.location - 1), abs(pitch.location + 1))
        pitcher[s.total_pitch_distance_from_call] += abs(pitch.location - pitch.target)
        pitcher[s.total_reduction] += pitch.reduction

    def update_swing(self, swing: hitting.Swing):
        batter = self.current_state.batter()
        batter[s.pitches_seen] += 1
        batter[s.total_strikes_against] += float(swing.strike)
        batter[s.total_fouls] += float(swing.foul)
        batter[s.total_hits] += float(swing.hit)
        batter[s.total_balls_taken] += float(swing.ball)
        batter[s.total_pitch_read_percent] += swing.read_chance

    def update_liveball(self, swing: liveball.HitBall):
        batter = self.current_state.batter()
        batter[s.total_hits] += 1
        batter[s.total_hit_distance] += swing.live.distance()
        batter[s.total_exit_velocity] += swing.live.speed
        batter[s.total_launch_angle] += swing.live.launch_angle
        batter[s.total_field_angle] += swing.live.field_angle

        if swing.homerun:
            batter[s.total_home_runs] += 1

    def update_runs_batted_in(self, runs_scored: Union[int, Decimal]):
        # TODO: this does not correctly measure RBIs in the case of errors, stolen home, etc.
        self.current_state.batter()[s.total_runs_seen_from_home] += runs_scored

