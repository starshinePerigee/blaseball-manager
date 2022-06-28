"""This module contains BallGame, which is responsible for managing games as they are played:
"""

from decimal import Decimal

from blaseball.playball.event import Update
from blaseball.playball.gamestate import GameState, GameTags, GameRules, BaseSummary
from blaseball.stats.lineup import Lineup
from blaseball.stats.stadium import Stadium
from blaseball.util.messenger import Messenger


class GameManagmentUpdate(Update):
    """This is a sublass for the purpose of keeping this distinct"""
    def __init__(self, text: str = None):
        super().__init__(text)


class BallGame:
    """The manager for a game of blaseball. This maintains its own internal gamestate, and sends out gameticks
    in response to all_game's "tick" on its messenger
    """
    def __init__(self, all_game_messenger: Messenger, home: Lineup, away: Lineup, stadium: Stadium, rules: GameRules):
        self.state = GameState(home, away, stadium, rules)
        self.needs_new_batter = [True, True]
        self.live_game = True

        # all_game_messenger.subscribe(self.send_tick, None)  # TODO

        self.messenger = Messenger()
        self.messenger.subscribe(self.score_runs, GameTags.runs_scored)
        self.messenger.subscribe(self.add_ball, GameTags.ball)
        self.messenger.subscribe(self.add_foul, GameTags.foul)
        self.messenger.subscribe(self.add_strike, GameTags.strike)
        self.messenger.subscribe(self.player_hit_ball, GameTags.hit_ball)
        self.messenger.subscribe(self.player_walked, GameTags.player_walked)
        self.messenger.subscribe(self.update_basepaths, GameTags.bases_update)
        self.messenger.subscribe(self.add_outs, GameTags.outs)

    def start_game(self):
        """Call this externally once everything has had a chance to subscribe to this messenger."""
        start_game_text = (f"{self.state.teams[0]['pitcher']['team']} vs. "
                           f"{self.state.teams[1]['pitcher']['team']}!")
        self.messenger.send(GameManagmentUpdate(start_game_text), [GameTags.game_updates, GameTags.game_start])

    def score_runs(self, runs: int):
        self.state.scores[self.state.offense_i()] += runs
        self.messenger.send(Update(self.state.score_string()), GameTags.game_updates)

    def add_ball(self):
        """Add a ball to the count, issue walk if needed"""
        self.state.balls += 1
        if self.state.balls >= self.state.rules.ball_count:
            self.messenger.send(Update(f"{self.state.count_string()}! {self.state.batter()['name']} issued a walk."),
                                GameTags.game_updates)
            self.messenger.send(self.state.batter(), GameTags.player_walked)
            self.increment_batter()
        else:
            self.messenger.send(Update("Ball. " + self.state.count_string()), GameTags.game_updates)

    def add_foul(self):
        """add a strike to the count, if applicable"""
        if self.state.strikes < self.state.rules.strike_count - 1:
            self.state.strikes += 1
        self.messenger.send(Update("Foul ball. " + self.state.count_string()), GameTags.game_updates)

    def add_strike(self, strike_swinging):
        """add a strike to the count, issue out if needed"""
        self.state.strikes += 1

        if strike_swinging:
            swing_text = "swinging"
        else:
            swing_text = "looking"

        if self.state.strikes < self.state.rules.strike_count:
            self.messenger.send(Update(f"Strike {swing_text}. {self.state.count_string()}"), GameTags.game_updates)
        else:
            self.messenger.send(Update(f"{self.state.batter()['name']} struck out {swing_text}."), GameTags.game_updates)
            self.increment_batter()
            self.messenger.send(1, GameTags.outs)

    def player_hit_ball(self, ball):
        self.increment_batter()

    def player_walked(self, player):
        self.increment_batter()

    def start_at_bat(self):
        self.state.strikes = 0
        self.state.balls = 0
        self.needs_new_batter[self.state.offense_i()] = False
        self.messenger.send(self.state.batter(), GameTags.new_batter)
        new_player_message = f"{self.state.batter()['name']} stepping up to bat."
        self.messenger.send(Update(new_player_message), GameTags.game_updates)

    def increment_batter(self):
        """queue up the next batter."""
        self.needs_new_batter[self.state.offense_i()] = True

        rollover = self.state.increment_batting_order()
        if rollover:
            self.messenger.send(tags=GameTags.cycle_batting_order)

    def update_basepaths(self, summary: BaseSummary):
        self.state.bases = summary

    def send_tick(self):
        """Send a new gamestate tick, calling for the next pitch."""
        if self.needs_new_batter[self.state.offense_i()]:
            self.start_at_bat()

        self.messenger.send(self.state, GameTags.state_ticks)

    def add_outs(self, outs):
        """Add a number of outs, will move game along."""
        self.state.outs += outs
        if self.state.outs >= self.state.rules.outs_count:
            self.end_half()

    def end_half(self):
        """Call for the end of a half inning and entire inning/game as needed"""
        if self.state.inning_half:
            # we're in the top of the inning
            self.state.inning_half -= 1
            self.messenger.send(self.state.inning_half, GameTags.new_half)
        else:
            if self.state.inning_half:
                self.next_half_inning()
            else:
                self.next_inning()

    def next_half_inning(self):
        """Start the half inning."""
        self.state.outs = 0
        self.state.inning_half -= 1
        self.messenger.send(self.state.inning_half, GameTags.new_half)
        # TODO: shame

    def next_inning(self):
        """Start the next inning"""
        self.messenger.send(GameManagmentUpdate(f"Inning {self.state.inning} is now an outing."), GameTags.game_updates)
        self.state.inning_half = 1
        self.state.inning += 1
        if self.state.inning > self.state.rules.innings and self.state.scores[0] != self.state.scores[1]:
            self.end_game()
        else:
            self.messenger.send(self.state.inning_half, GameTags.new_half)
            self.messenger.send(self.state.inning, GameTags.new_inning)

    def end_game(self):
        self.live_game = False
        game_end = (f"Game over! Final score: "
                    f"{self.state.teams[0]['pitcher']['team']} {self.state.scores[0]}, "
                    f"{self.state.teams[1]['pitcher']['team']} {self.state.scores[1]}.")
        self.messenger.send(GameManagmentUpdate(game_end), [GameTags.game_updates, GameTags.game_over])


"""
Game flow:
Ballgame
    Innings
        Inning Halfs
            At-Bats
                Ticks
                
Ticks: each game event. Distinguished by state_ticks messages and invocations of send_tick

At-bats: a single player's at-bat. Distinguished by new_batter messages.
        separated by calls of start_at_bat.
        
        because we want a player to step up at the start of a tick, increment_batter sets the
        needs_new_batter[i] flag, which causes them to step up at the start of a tick.
        this flag is kicked by hits, strikeouts, walks, and the start of innings/the game.
        
Inning halfs: a single team's three outs in an inning. Distinguished by new_half, managed by next_half_inning.

Innings: distinguished by *both* new_half and new_inning. managed by next_half_inning

Ballgame: started with start_game, ended with end_game.

An inning transition looks like this:
- a player is marked out by pitchmanager or add_strike.
- if it's add_strike, add_strike updates the "need new batter" flag and increments the batter.
- add_outs adds the out, then because this is enough outs, it calls end_half
 - end half sends both new_half and new_inning
- this triggers next_half and next_half_inning
"""

if __name__ == "__main__":
    from time import sleep
    from blaseball.util import quickteams
    from blaseball.playball.pitchmanager import PitchManager
    from blaseball.util.messenger import Listener
    g = quickteams.game_state

    print(quickteams.league[0])
    print(g.home_team.string_summary())
    print("\r\n\t\t* * * VS * * *\r\n")
    print(quickteams.league[1])
    print(g.away_team.string_summary())

    sleep(3)

    class UpdatePrinter(Listener):
        def respond(self, argument):
            if argument.text is not None:
                print(argument.text)

    class NewlinePrinter(Listener):
        def respond(self, argument):
            print("")

    null_manager = Messenger()
    bg = BallGame(null_manager, g.home_team, g.away_team, g.stadium, g.rules)
    p = UpdatePrinter(bg.messenger, GameTags.game_updates)
    np = NewlinePrinter(bg.messenger, [GameTags.new_batter, GameTags.new_inning, GameTags.new_half])
    pm = PitchManager(bg.state, bg.messenger)

    bg.start_game()

    while bg.live_game:
        bg.send_tick()
