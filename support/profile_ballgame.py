import cProfile
import pstats

from blaseball.playball.ballgame import BallGame
from blaseball.playball.gamestate import GameTags
from blaseball.util import quickteams
from blaseball.playball.pitchmanager import PitchManager
from blaseball.util.messenger import Listener, Messenger


class SaveEvents(Listener):
    def __init__(self, messenger, tags):
        self.messages = []
        super().__init__(messenger, tags)

    def respond(self, argument):
        self.messages += [argument.text]

    def print_all(self):
        for i, message in enumerate(self.messages):
            print(f"{i}: {message}")


g = quickteams.game_state

null_manager = Messenger()
bg = BallGame(null_manager, g.home_team, g.away_team, g.stadium, g.rules)
se = SaveEvents(bg.messenger, GameTags.game_updates)
pm = PitchManager(bg.state, bg.messenger)

bg.start_game()

profiler = cProfile.Profile()
profiler.enable()

while bg.live_game:
    bg.send_tick()
    if bg.tick_count >= 200:
        break

profiler.disable()
stats = pstats.Stats(profiler).sort_stats('tottime')

se.print_all()
print("\r\n\r\n~~~~~~~~~~~\r\n\r\n")

stats.print_stats()


# speed before stats refactor:
"""
         417821 function calls (416868 primitive calls) in 0.268 seconds
         410651 function calls (409712 primitive calls) in 0.283 seconds
         422302 function calls (421354 primitive calls) in 0.352 seconds
         424616 function calls (423667 primitive calls) in 0.288 seconds
         417747 function calls (416808 primitive calls) in 0.285 seconds
"""

# after stats refactor!
"""
         166491 function calls (163942 primitive calls) in 0.097 seconds
         164334 function calls (161828 primitive calls) in 0.096 seconds
         163885 function calls (161392 primitive calls) in 0.089 seconds
         160630 function calls (158223 primitive calls) in 0.088 seconds
         164786 function calls (162278 primitive calls) in 0.099 seconds
"""

# wao 3x speedup :v