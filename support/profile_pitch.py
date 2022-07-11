import cProfile
import pstats

from blaseball.playball.pitching import Pitch
from blaseball.util import quickteams

g = quickteams.game_state
pitcher = g.defense()['pitcher']
catcher = g.defense()['catcher']

profiler = cProfile.Profile()
profiler.enable()

pitches_1000 = [Pitch(g, pitcher, catcher) for __ in range(1000)]

profiler.disable()
stats = pstats.Stats(profiler).sort_stats('tottime')

stats.print_stats()
