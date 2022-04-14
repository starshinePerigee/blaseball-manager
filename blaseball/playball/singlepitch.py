"""
This is a single pitch in a game, from the "commit to pitch" (no actions) to the result

The result can be a live ball, or an updated game state.
"""

from blaseball.playball.pitching import Pitch
from blaseball.playball.hitting import Swing
from blaseball.playball.ballgame import BallGame
from blaseball.playball.event import Event

from typing import List

# TODO: either move liveball out somewhere else (like in here) or make hitting pass only a hit quality
# TODO: maybe move liveball to hitting, and liveball init takes hit quality?
# TODO: iunno

class PitchHit(Event):
    """
    A single pitch, from after the action timing window, to the result of the pitch.
    This is carried back to the game as a Ball.


    """
    def __init__(self, game: BallGame):
        super().__init__(f"{game.defense()['pitcher']} pitch to {game.batter()}")

        # TODO: This is going to need a lot of work to make nice and pretty, describe the pitch, etc.
        # this is a very quick pass to make things work.
        self.text = []

        # pitch the ball
        self.pitch = Pitch(
            game,
            game.defense()['pitcher'],
            game.defense()['catcher']
        )
        # maybe describe the pitch some?

        # batter decides swing
        self.live = None
        self.swing = Swing(game, self.pitch, game.batter())
        if self.swing:
            if self.swing.strike:
                self.text += ["Strike, swinging."]
                self.text += [game.add_strike()]
            elif self.swing.foul:
                self.text += ["Foul ball."]
                self.text += [game.add_foul()]
            else:
                self.text += ["It's a hit!"]  # maybe expand this some?
                self.live = self.swing.live
                self.text += [str(self.swing.live)]
        else:
            # batter does not swing
            if self.swing.strike:
                self.text += ["Strike, looking."]
                self.text += [game.add_strike()]
            else:
                self.text += ["Ball."]
                self.text += [game.add_ball()]

    def feed_text(self, debug=False) -> List[str]:
        if debug:
            string = []
            string += [f"Pitch: {self.pitch}"]
            string += [f"Swing: {self.swing}"]
            if self.swing:
                string += [f"Hit: {self.swing.live}"]
            return string
        else:
            return self.text


if __name__ == "__main__":
    from blaseball.stats import players, teams, stats
    from blaseball.stats.lineup import Lineup
    from data import teamdata
    pb = players.PlayerBase()
    team_names = teamdata.TEAMS_99
    league = teams.League(pb, team_names[5:7])
    print('setup complete..\r\n')

    l1 = Lineup("Home Lineup")
    l1.generate(league[0])
    l2 = Lineup("Away Lineup")
    l2.generate(league[1])

    g = BallGame(l1, l2, False)
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
        furthest_hit = 0
        furthest_swing = None
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
                if p.live.distance() > furthest_hit:
                    furthest_hit = p.live.distance()
                    furthest_swing = p.swing
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
        print(f"Furthest hit is {furthest_hit:.0f} ft, "
              f"with a quality of {furthest_swing.hit_quality:.2f}, exit velocity {furthest_swing.live.speed:.0f} mph, "
              f"and launch angle {furthest_swing.live.launch_angle:.0f}")

    PITCHES = 1000
    g.batter()['power'] = 1
    run_test(PITCHES)
    print("x")
