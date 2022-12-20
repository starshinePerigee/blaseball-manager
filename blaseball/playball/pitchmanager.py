"""
This is a Listener that responds to BallGame GameState ticks.
"""

from blaseball.util.messenger import Messenger
from blaseball.playball.event import Update
from blaseball.playball.pitching import Pitch
from blaseball.playball.hitting import Swing
from blaseball.playball.liveball import HitBall
from blaseball.playball.inplay import FieldBall
from blaseball.playball.basepaths import Basepaths
from blaseball.playball.gamestate import GameState, BaseSummary
from blaseball.playball.gamestate import GameTags as Tags
from blaseball.stats.players import Player
from blaseball.stats import stats as s


class PitchManager:
    def __init__(self, initial_state: GameState, messenger: Messenger):
        """This instantiates the messenger and sets it to listen to gamestate ticks."""
        # instantiate some heavier classes for reuse here:
        self.basepaths = Basepaths(initial_state.stadium)
        # todo: live defense?

        self.messenger = messenger
        self.messenger.subscribe(self.pitchhit, Tags.state_ticks)
        self.messenger.subscribe(self.update_basepaths, Tags.bases_update)
        self.messenger.subscribe(self.player_walk, Tags.player_walked)

    def pitchhit(self, game: GameState):
        pitch = Pitch(
            game,
            game.defense()['pitcher'],
            game.defense()['catcher'],
            self.messenger
        )

        batter = game.batter()

        swing = Swing(game, pitch, batter)
        self.messenger.send(swing, [Tags.swing])
        # BallGame is responsible for handling non-hits

        if not swing.hit:
            if swing.strike:
                self.messenger.send(swing.did_swing, Tags.strike)
            elif swing.foul:
                self.messenger.send(tags=Tags.foul)
            elif swing.ball:
                self.messenger.send(tags=Tags.ball)
        else:
            hit_ball = HitBall(game, swing.hit_quality, pitch.reduction, batter)
            self.messenger.send(hit_ball, [Tags.hit_ball, Tags.game_updates])

            if hit_ball.homerun:
                self.messenger.send(len(game.bases) + 1, [Tags.home_run, Tags.runs_scored])
                self.messenger.send(BaseSummary(game.stadium.NUMBER_OF_BASES), Tags.bases_update)
            else:
                self.basepaths.load_from_summary(game.bases)
                self.basepaths.reset_all(game.defense()['pitcher'], game.defense()['catcher'])
                field_ball = FieldBall(batter, game.defense().defense, hit_ball.live, self.basepaths)

                for update in field_ball.updates:
                    self.messenger.send(update, [Tags.game_updates])

                if field_ball.runs > 0:
                    self.messenger.send(field_ball.runs, [Tags.runs_scored])
                if field_ball.outs:
                    self.messenger.send(field_ball.outs, [Tags.outs])

                self.messenger.send(BaseSummary(basepaths=self.basepaths), [Tags.bases_update])

    def update_basepaths(self, summary: BaseSummary):
        self.basepaths.load_from_summary(summary)

    def player_walk(self, player: Player):
        runs_scored, players_scoring = self.basepaths.walk_batter(player)
        if runs_scored:
            walk_string = f"{players_scoring[0][s.name]} walked in for a run!"
            self.messenger.send(Update(walk_string), Tags.game_updates)
            self.messenger.send(runs_scored, Tags.runs_scored)
        self.messenger.send(BaseSummary(basepaths=self.basepaths), Tags.bases_update)
