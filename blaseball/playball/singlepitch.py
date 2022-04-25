"""
This is a single pitch in a game, from the "commit to pitch" (no actions) to the result

The result can be a live ball, or an updated game state.
"""

from blaseball.playball.pitching import Pitch
from blaseball.playball.hitting import Swing
from blaseball.playball.liveball import HitBall, LiveBall
from blaseball.playball.fielding import FieldBall
from blaseball.playball.ballgame import BallGame
from blaseball.playball.event import Event

from typing import List


class PitchHit(Event):
    """
    A single pitch, from after the action timing window, to the result of the pitch.
    This is carried back to the game as a Ball.


    """
    def __init__(self, game: BallGame):
        super().__init__(f"{game.defense()['pitcher']} pitch to {game.batter()}")

        # TODO: This is going to need a lot of work to make nice and pretty, describe the pitch, etc.
        # this is a very quick pass to make things work.

        # pitch the ball
        self.pitch = Pitch(
            game,
            game.defense()['pitcher'],
            game.defense()['catcher']
        )
        self.updates += [self.pitch]

        # batter decides swing
        self.swing = Swing(game, self.pitch, game.batter())
        self.updates += [self.swing]

        if self.swing.strike:
            self.updates += [game.add_strike()]
        if self.swing.ball:
            self.updates += [game.add_ball()]
        if self.swing.foul:
            self.updates += [game.add_foul()]

        # handle the hit
        if self.swing.hit:
            self.live = HitBall(game, self.swing, game.batter())
            self.updates += [self.live]
            if self.live.homerun:
                self.fielding = None
            else:
                self.fielding = FieldBall(game, self.live)
                # TODO
        else:
            self.live = None
            self.fielding = None

    def field_ball(self, live: LiveBall):
        pass

    def feed_text(self, debug=False) -> List[str]:
        if debug:
            string = []
            string += [f"Pitch: {self.pitch}"]
            string += [f"Swing: {self.swing}"]
            if self.live:
                string += [f"Hit: {self.live}"]
            return string
        else:
            super().feed_text()


if __name__ == "__main__":
    from blaseball.stats import stats

    from blaseball.util import quickteams
    g = quickteams.ballgame

    g.balls = 1

    test_pitcher = g.defense()['pitcher']
    print(f"Pitcher: {test_pitcher}")
    for s in stats.all_stats['rating']:
        if s.category == 'pitching':
            print(f"{s}: {test_pitcher._to_stars(test_pitcher[s.name])}")
    test_catcher = g.defense()['catcher']
    print(f"Catcher: {test_catcher}")
    print(f"Calling: {test_catcher._to_stars(test_catcher['calling'])}")
    print("")
    test_batter = g.batter()
    print(f"Batter: {test_batter}")
    for s in stats.all_stats['rating']:
        if s.category == 'batting':
            print(f"{s}: {test_batter._to_stars(test_batter[s.name])}")

    print("\r\n* * * * * \r\n\r\n")
    p = PitchHit(g)
    print("\r\n".join(p.feed_text(True)))
    print("")

    for _ in range(0, 9):
        p = PitchHit(g)
        print("\r\n".join(p.feed_text()))
        print("")

    for _ in range(0, 99):
        p = PitchHit(g)
        if p.swing.live:
            print(p.swing)
            print(f"{p.swing.live.distance():.0f} feet.")

    def run_test(pitches):
        strikes = 0
        balls = 0
        fouls = 0
        hit_count = 0
        quality = 0
        distance = 0
        location = 0
        obscurity = 0
        difficulty = 0
        hits = []
        for _ in range(0, pitches):
            p = PitchHit(g)
            strikes += int(p.swing.strike)
            balls += int(p.swing.ball)
            fouls += int(p.swing.foul)
            hit_count += int(bool(p.live))
            location += p.pitch.location
            obscurity += p.pitch.obscurity
            difficulty += p.pitch.difficulty
            if p.live:
                hits += [p.live]
                quality += p.swing.hit_quality
                distance += p.live.distance()
        strike_rate = strikes / pitches * 100
        ball_rate = balls / pitches * 100
        foul_rate = fouls / pitches * 100
        hit_rate = hit_count / pitches * 100
        quality /= len(hits)
        distance /= len(hits)
        location /= pitches
        obscurity /= pitches
        difficulty /= pitches
        ave_la = sum([x.launch_angle for x in hits])/len(hits)
        ave_fa = sum([x.field_angle for x in hits])/len(hits)
        ave_speed = sum([x.speed for x in hits])/len(hits)
        print(f"Strike rate: {strike_rate:.0f}%, ball rate: {ball_rate:.0f}%, foul rate: {foul_rate:.0f}% hit rate: {hit_rate:.0f}%")
        print(f"{len(hits)} hits. Average: quality {quality:.2f}, distance {distance:.0f}, "
              f"launch angle {ave_la:.0f}, field angle {ave_fa:.0f}, speed {ave_speed:.0f}")
        print(f"Ave location: {location:.2f}, ave obscurity: {obscurity:.2f}, ave difficulty {difficulty:.2f}.")

    PITCHES = 1000
    g.batter()['power'] = 1
    run_test(PITCHES)
    print("x")
