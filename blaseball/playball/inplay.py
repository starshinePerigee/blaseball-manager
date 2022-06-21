"""
Inplay handles everything that happens once a ball is hit.

At its core, it creates a second Event (so a hit ball is two events, each with their own series of updates.

This commands BasePaths and interfaces with fielding as needed..
"""

from blaseball.playball.basepaths import Runner, Basepaths, calc_speed
from blaseball.playball.fielding import Catch, Throw, calc_throw_duration_base
from blaseball.playball.ballgame import BallGame
from blaseball.playball.liveball import LiveBall
from blaseball.playball.event import Update
from blaseball.stats.players import Player
from blaseball.stats.lineup import Defense
from blaseball.util.geometry import Coord

from numpy.random import normal, rand
from typing import List, Tuple


class LiveDefense:
    """This class tracks and manages the defense for an entire ball in play."""
    def __init__(self, defense: Defense, base_locations: List[Coord]):
        self.defense = defense
        self.base_locations = base_locations

        self.fielder = None
        self.location = None

    def catch_liveball(self, ball: LiveBall, batter: Player) -> Tuple[Update, float, bool]:
        """"""
        self.location = ball.ground_location()
        fielder_position, distance = self.defense.closest(self.location)
        self.fielder = fielder_position.player
        catch = Catch(ball, self.fielder, distance)

        if catch.caught:
            catch_update = CatchOut(self.fielder, batter)
        else:
            catch_update = catch

        return catch_update, catch.duration, catch.caught

    def throw_to_base(self, target_base: int) -> Tuple[Update, float]:
        target_location = self.base_locations[target_base]
        position, distance = self.defense.closest(target_location)
        receiver = position.player

        if receiver is self.fielder:
            # tag the base?
            run_time = distance / calc_speed(self.fielder['speed'])
            return Update(f"{self.fielder['name']} tags base {target_base}"), run_time

        throw = Throw(self.fielder, receiver, distance)
        self.location = target_location
        self.fielder = receiver

        return throw, throw.duration

    DECISION_FUZZ_STDV = 0.5
    PROBABILITY_WINDOW = 2  # how much time you need to be 100% confident of a throw

    def calc_throw_time_differential(self, runner: Runner) -> float:
        """calculate the net time if a perfect throw attempt is made at Runner.
        Negative time means the runner wins, positive time means the fielder wins (assuming no errors)"""
        distance = self.location.distance(self.base_locations[runner.next_base()])
        throw_duration = calc_throw_duration_base(self.fielder['throwing'], distance)
        time_to_base = runner.time_to_base()
        return throw_duration - time_to_base

    def prioritize_runner(self, runner: Runner) -> float:
        """Determines a weight for a runner based on value and probability."""
        # base weight (pun intended):
        base_weight = runner.next_base()

        # fuzz time estimation
        time_fuzz = normal(0, LiveDefense.DECISION_FUZZ_STDV * (2 - self.fielder['awareness']))
        # if runner time >>> duration, this evaluates to 0. if duration >>> runner time, this evaluate to 1.
        # if 0 < delta < PROBABILITY_WINDOW this evalutes to somewhere between 0 and 1 continuously
        net_time = (self.calc_throw_time_differential(runner) + time_fuzz) / LiveDefense.PROBABILITY_WINDOW
        odds = max(0.0, min(1.0, net_time))
        return odds * base_weight

    def fielders_choice(self, active_runners: List[Runner]) -> int:
        """Decide which base to throw to based on the list of runners"""
        runners = [(self.prioritize_runner(runner), runner) for runner in active_runners]
        runners.sort(key=lambda x: x[0])
        return runners[0][1].next_base()

    def __str__(self):
        return f"Fielder, currently {self.fielder['name']} at {self.location}"

    def __repr__(self):
        return f"<{str(self)}>"


class CatchOut(Update):
    def __init__(self, fielder: Player, batter: Player):
        super().__init__(f"{batter['name']} hit a flyout to {fielder['name']}")


class FieldingOut(Update):
    def __init__(self, fielder: Player, runner: Runner, throw: bool = True):
        verb = "thrown" if throw else "tagged"
        if runner.forward:
            base = runner.base + 1
        else:
            base = runner.base
        super().__init__(f"{runner.player['name']} {verb} out at base {base} by {fielder['name']}.")


class Rundown(Update):
    pass


class RunScored(Update):
    def __init__(self, runner: Player):
        super().__init__(f"{runner['name']} scored!")


class FieldBall:
    def __init__(self, batter: Player, defense: Defense, live_ball: LiveBall, basepaths: Basepaths):
        self.runs = 0
        self.outs = 0
        self.updates = []

        fielder = Fielder(defense, basepaths.base_coords)
        catch = fielder.catch(live_ball)
        self.updates += [catch]
        if catch.caught:
            self.updates += [CatchOut(fielder.fielder, batter)]
            self.outs += 1
            basepaths.tag_up_all()
        else:
            basepaths += batter

        distance_to_home = live_ball.ground_location().distance(Coord(0, 0))
        throw_time = calc_throw_duration_base(fielder.fielder['throwing'], distance_to_home) - 1  # cut it a little short
        runs, scoring_runners = basepaths.advance_all(catch.duration, throw_time)
        self.runs += runs
        self.updates += [RunScored(runner) for runner in scoring_runners]

        while basepaths:
            active_runners = [runner for runner in basepaths.runners if runner]
            target = fielder.fielders_choice(active_runners)

            # a rundown occurs when:
            # fielder is on a base
            # throwing it one base forward or backwards
            # with a player in between
            # who is not out

            updates, throw_duration = fielder.throw(target)
            self.updates += [updates]

            outs, players_out = basepaths.check_out(target)
            self.outs += outs
            self.updates += [FieldingOut(fielder.fielder, runner, not tagable) for runner, tagable in players_out]

            new_runs, runners_scoring = basepaths.advance_all(throw_duration)
            self.runs += new_runs
            self.updates += [RunScored(runner) for runner in runners_scoring]

        if len(self.updates) < 2:
            self.updates += [self.filler_text(basepaths.runners[-1])]

    def filler_text(self, runner: Runner) -> Update:
        BASE_LENGTH = {
            1: "single.",
            2: "double.",
            3: "triple!",
            4: "quadruple!!"
        }
        return Update(f"{runner.player['name']} hit a {BASE_LENGTH[runner.base]}")


if __name__ == "__main__":
    from blaseball.util import quickteams
    g = quickteams.ballgame

    # TODO - quick demo

#     infield_fly = LiveBall(30, 70, 90)
#
#
#     def field_ball(ball, batter):
#         fb = FieldBall(g.batter(batter), g.defense().defense, ball, g.bases)
#
#         for update in fb.updates:
#             print(update.text)
#         print(g.bases.nice_string())
#         print("")
#
#     field_ball(infield_fly, 0)
#     field_ball(infield_fly, 1)
#     field_ball(infield_fly, 2)
#
#     close_ground = LiveBall(-30, 15, 90)
#
#     field_ball(close_ground, 3)
#     field_ball(close_ground, 4)
#     field_ball(close_ground, 5)