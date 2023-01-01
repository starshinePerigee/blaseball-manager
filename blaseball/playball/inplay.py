"""
Inplay handles everything that happens once a ball is hit.

At its core, it creates a second Event (so a hit ball is two events, each with their own series of updates.

This commands BasePaths and interfaces with fielding as needed.
"""

from blaseball.playball.basepaths import Runner, Basepaths, calc_speed
from blaseball.playball.fielding import Catch, Throw, calc_throw_duration_base
from blaseball.playball.gamestate import GameState
from blaseball.playball.liveball import LiveBall
from blaseball.playball.event import Update
from blaseball.stats.players import Player
from blaseball.stats.lineup import Defense
from blaseball.stats import stats as s
from blaseball.util.geometry import Coord

from numpy.random import normal, rand
from typing import List, Tuple
from loguru import logger


class LiveDefense:
    """This class tracks and manages the defense for an entire ball in play."""
    def __init__(self, defense: Defense, base_locations: List[Coord]):
        self.defense = defense
        self.base_locations = base_locations

        self.fielder = None  # Player who has the ball
        self.location = None  # coordinate location of the ball

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
            # tag the base - if this returns 0 FieldBall will initiate a rundown.
            run_time = distance / calc_speed(self.fielder['speed'])
            return Update(f"{self.fielder['name']} tags base {target_base}"), run_time

        throw = Throw(self.fielder, receiver, distance)
        self.location = target_location
        self.fielder = receiver

        return throw, throw.duration

    DECISION_FUZZ_STDV = 0.5
    PROBABILITY_WINDOW = 1.5  # how much time you need to be 100% confident of a throw
    NOT_BASE_WEIGHT = 1  # the inverse of how much to weight the current base. Higher means players take the safe throw
    # more often, lower means they throw to third mor often.

    def calc_throw_time_ratio(self, runner: Runner) -> float:
        """calculate how much of a time advantage has if perfect throw attempt is made at Runner.
        This is a percentage, from 0 to +.
        ratio less than 1 means the runner wins, ratio greater than 1 means the fielder wins (assuming no errors."""
        distance = self.location.distance(self.base_locations[runner.next_base()])
        throw_duration = calc_throw_duration_base(self.fielder['throwing'], distance)
        if throw_duration == 0:
            return 100  # avoid div/0 errors
        time_to_base = runner.time_to_base()
        return time_to_base / throw_duration

    def prioritize_runner(self, runner: Runner) -> float:
        """Determines a weight for a runner based on value and probability."""
        # base weight (pun intended):
        base_weight = runner.next_base()

        # fuzz time estimation
        time_fuzz = normal(0, LiveDefense.DECISION_FUZZ_STDV * (2 - self.fielder['awareness']))
        # if runner time >>> duration, this evaluates to high. if duration >>> runner time, this evaluate to 0
        # (or negative).
        # if 0 < delta < PROBABILITY_WINDOW this evalutes to somewhere between 0 and 1 continuously
        net_time = (self.calc_throw_time_ratio(runner) + time_fuzz) / LiveDefense.PROBABILITY_WINDOW
        odds = max(0.0, min(1.0, net_time))
        return odds * (base_weight + LiveDefense.NOT_BASE_WEIGHT)

    def fielders_choice(self, active_runners: List[Runner]) -> int:
        """Decide which base to throw to based on the list of runners"""
        runners = [(self.prioritize_runner(runner), runner) for runner in active_runners]
        runners.sort(key=lambda x: x[0], reverse=True)
        return runners[0][1].next_base()

    RUNDOWN_FORWARD_WEIGHT = 1
    RUNDOWN_BACKwARD_WEIGHT = 1
    RUNDOWN_RUNNER_WEIGHT = 1
    RUNDOWN_MAX_BALLAST = 1  # higher numbers mean skill has lower effect

    @staticmethod
    def roll_rundown_out(runner_bravery, primary_basepeep_bravery, support_basepeep_bravery) -> float:
        """Roll to see if a runner in a rundown is out.
        higher odds mean better chances for the runner
        this means that if this is positive, the defenders win
        """
        defending_bravery = primary_basepeep_bravery * LiveDefense.RUNDOWN_FORWARD_WEIGHT
        defending_bravery += support_basepeep_bravery * LiveDefense.RUNDOWN_BACKwARD_WEIGHT
        runner_bravery = runner_bravery * LiveDefense.RUNDOWN_RUNNER_WEIGHT
        offensive_advantage = runner_bravery + LiveDefense.RUNDOWN_MAX_BALLAST / 2
        defensive_advantage = defending_bravery + LiveDefense.RUNDOWN_MAX_BALLAST / 2

        odds = offensive_advantage / (offensive_advantage + defensive_advantage)
        return rand() - odds

    @staticmethod
    def roll_rundown_advance(runner_bravery, forward_basepeep_bravery) -> bool:
        runner_advantage = runner_bravery + LiveDefense.RUNDOWN_MAX_BALLAST / 2
        defender_advantage = runner_bravery + forward_basepeep_bravery + LiveDefense.RUNDOWN_MAX_BALLAST
        return rand() >= runner_advantage / defender_advantage

    BASE_TIME = 1  # how many seconds for a single pass rundown
    TIMING_TIME_MODIFIER = 2  # bonus delay for the runner's time

    @staticmethod
    def calc_wasted_time(timing: float, rundown_roll: float) -> float:
        time_multiplier = 1 / (abs(rundown_roll) + 0.5)  # 0.6 to 2
        time_multiplier *= (timing + 1) * LiveDefense.TIMING_TIME_MODIFIER
        return LiveDefense.BASE_TIME * time_multiplier

    def run_rundown(self, basepaths: Basepaths, base: int) -> Tuple[List[Update], int, float]:
        # runner = basepaths.runners[]
        runner = basepaths.get_runner_approaching_base(base)
        if runner.tagging_up:
            base_forward = base + 1
            base_backward = base
            support_basepeep = self.defense.closest(self.base_locations[base_forward])[0].player
            forward_basepeep = support_basepeep
            extra_str = " while tagging up"
        else:
            base_forward = base
            base_backward = base - 1
            support_basepeep = self.defense.closest(self.base_locations[base_backward])[0].player
            forward_basepeep = self.fielder
            extra_str = ""

        primary_basepeep = self.fielder

        updates = [Update(f"{runner.player[s.name]} is caught in a rundown between "
                          f"{primary_basepeep[s.name] and support_basepeep[s.name]}{extra_str}!")]

        outs = 0
        rundown_roll = LiveDefense.roll_rundown_out(
            runner.player[s.bravery],
            primary_basepeep[s.bravery],
            support_basepeep[s.bravery]
        )
        if rundown_roll >= 0:
            # runner loses!
            updates += [Update(f"{runner.player[s.name]} is caught! They are out!")]
            basepaths.mark_out(runner)
            outs = 1
        else:
            # check to see if advance or retreat:
            if LiveDefense.roll_rundown_advance(runner.player[s.bravery], forward_basepeep[s.bravery]):
                updates += [Update(f"{runner.player[s.name]} makes it forward!")]
                runner.touch_base(base_forward)
                runner.hold()
            else:
                updates += [Update(f"{runner.player[s.name]} is driven backwards, but makes it safe!")]
                runner.touch_base(base_backward)
                runner.hold()

        wasted_time = LiveDefense.calc_wasted_time(runner.player[s.timing], rundown_roll)
        if wasted_time > 1:
            updates += [Update(f"{wasted_time} seconds were wasted.")]

        return updates, outs, wasted_time

    def __str__(self):
        return f"Fielder, currently {self.fielder['name']} at {self.location}"

    def __repr__(self):
        return f"<{str(self)}>"


class CatchOut(Update):
    def __init__(self, fielder: Player, batter: Player):
        # todo: desribe catch location
        super().__init__(f"{batter['name']} hit a flyout to {fielder['name']}")


class FieldingOut(Update):
    def __init__(self, fielder: Player, runner: Runner, throw: bool = True):
        verb = "thrown" if throw else "tagged"
        if runner.forward:
            base = runner.base + 1
        else:
            base = runner.base
        super().__init__(f"{runner.player['name']} {verb} out at base {base} by {fielder['name']}.")


class RunScored(Update):
    def __init__(self, runner: Player):
        super().__init__(f"{runner['name']} scored!")


class FieldBall:
    def __init__(self, batter: Player, defense: Defense, live_ball: LiveBall, basepaths: Basepaths):
        self.runs = 0
        self.outs = 0
        self.updates = []

        live_defense = LiveDefense(defense, basepaths.base_coords)
        catch_update, catch_duration, caught = live_defense.catch_liveball(live_ball, batter)
        self.updates += [catch_update]
        if caught:
            self.outs += 1
            basepaths.tag_up_all()
        else:
            basepaths += batter

        distance_to_home = live_ball.ground_location().distance(Coord(0, 0))
        throw_time = calc_throw_duration_base(live_defense.fielder['throwing'], distance_to_home) - 1
        # the minus one is cut it a little short to encourage people make mistakes, it's a magic spice number
        runs, scoring_runners = basepaths.advance_all(catch_duration, throw_time)
        self.runs += runs
        self.updates += [RunScored(runner) for runner in scoring_runners]

        while basepaths:
            active_runners = [runner for runner in basepaths.runners if runner]
            target = live_defense.fielders_choice(active_runners)

            # a rundown occurs when:
            # fielder is on a base
            # throws it to themselves
            # and it's not a force out

            throw_update, throw_duration = live_defense.throw_to_base(target)
            initiate_rundown = throw_duration <= 0.05
            self.updates += [throw_update]

            new_runs, runners_scoring = basepaths.advance_all(throw_duration)
            self.runs += new_runs
            self.updates += [RunScored(runner) for runner in runners_scoring]

            player_out, tagged_out = basepaths.check_out(target)
            if player_out:
                self.outs += 1
                self.updates += [FieldingOut(live_defense.fielder, player_out, not tagged_out)]
            elif initiate_rundown:
                self.do_rundown(basepaths, live_defense, target)

        if not caught and len(self.updates) < 2:
            if len(basepaths.runners) > 0:
                self.updates += [self.filler_text(basepaths.runners[-1])]
            else:
                self.updates += [Update("Whoops, batter vanished into a secret base???")]
                logger.warning("Player vanished into a secret base.")

    def do_rundown(self, basepaths: Basepaths, live_defense: LiveDefense, target: int) -> None:
        """Execute a rundown, which is complicated enough to need its own function."""

        rundown_updates, rundown_outs, rundown_duration = live_defense.run_rundown(basepaths, target)
        self.outs += rundown_outs
        self.updates += [rundown_updates]

        # if the rundown runner makes it home, they'll touch base, hold, and get scored here:
        rundown_runs, runners_scoring = basepaths.advance_all(rundown_duration)
        self.runs += rundown_runs
        self.updates += [RunScored(runner) for runner in runners_scoring]

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
    g = quickteams.game_state

    infield_fly = LiveBall(30, 70, 90)


    def field_ball(ball, batter):
        fb = FieldBall(g.batter(batter), g.defense().defense, ball, g.bases)

        for update in fb.updates:
            if update.text is not None:
                print(update.text)
        print(g.bases.nice_string())
        print("")

    field_ball(infield_fly, 0)
    field_ball(infield_fly, 1)
    field_ball(infield_fly, 2)

    close_ground = LiveBall(-30, 15, 90)

    field_ball(close_ground, 3)
    field_ball(close_ground, 4)
    field_ball(close_ground, 5)