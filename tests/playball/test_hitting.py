import pytest
import statistics

from blaseball.playball import hitting, pitching


class TestHitting:

    DESPERATION_UPPER_BOUND = 1.4
    DESPERATION_LOWER_BOUND = 0

    @pytest.mark.parametrize(
        "count, limit, absolute",
        #  using absolute as a parameter is kind of a jank idea, this should have been two tests. see below.
        [
            ((0, 0), (1, 1.1), True),
            ((1, 0), (0, 1), True),
            ((0, 0), (1, 0), False),
            ((1, 0), (2, 0), False),
            ((2, 0), (3, 0), False),
            ((3, 1), (3, 0), False),
            ((3, 2), (1, 2), True),
            ((0, 1), (1, 2), True),
        ]
    )
    def test_calc_desperation(self, count, limit, absolute):
        # first pitch should be a strike: mlb first pitch strike rate is 58%
        desperation = hitting.calc_desperation(count[0], count[1])
        if absolute:
            assert limit[0] < desperation < limit[1]
        else:
            limit = hitting.calc_desperation(limit[0], limit[1])
            assert desperation > limit
            assert TestHitting.DESPERATION_LOWER_BOUND < limit < TestHitting.DESPERATION_UPPER_BOUND
        assert TestHitting.DESPERATION_LOWER_BOUND < desperation < TestHitting.DESPERATION_UPPER_BOUND

    def test_calc_desperation_strikes(self):
        assert hitting.calc_desperation(0, 2) == pytest.approx(hitting.calc_desperation(0, 1))

    def test_print_calc_desperation(self):
        print(" ~Desperation~")
        print(f"0-0: {hitting.calc_desperation(0, 0)}")
        print(f"Count max positive: {hitting.calc_desperation(0, 2)}")
        print(f"Count max negative: {hitting.calc_desperation(3, 0)}")
        print(f"3-2: {hitting.calc_desperation(3, 2)}")

    @pytest.mark.parametrize(
        "greater, lesser",
        [
            ((0, 0), (1, 0)),
            ((1, 1), (1, 0))
        ]
    )
    def test_calc_read_chance_comparison(self, greater, lesser):
        assert hitting.calc_read_chance(greater[0], greater[1]) > hitting.calc_read_chance(lesser[0], lesser[1])

    @pytest.mark.parametrize(
        "obscurity, discipline, low, high",
        [
            (0, 1, 0.95, 1),
            (3, 0, 0, 0.5),  # if you're bad enough and if the pitcher is good enough you do worse than just guessing.
            (1, 1, 0.6, 0.8)  # MLB odds are about 70% for reading the average pitch
        ]
    )
    def test_calc_read_chance_absolute(self, obscurity, discipline, low, high):
        # obscurity ranges from 0 to 3, but average is between 0.5 and 1
        assert low <= hitting.calc_read_chance(obscurity, discipline) <= high

    def test_print_calc_read_chance(self):
        print(" ~Read Chance~")
        obscurities = [0, 0.5, 1, 3]
        disciplines = [0, 0.5, 1, 2]
        print(f"Read chance vs obscurity ({disciplines} discipline)")
        for obscurity in obscurities:
            print_str = f"* {obscurity:0.1f} *  "
            for discipline in disciplines:
                print_str += f"{hitting.calc_read_chance(obscurity, discipline)*100: >3.0f}%  "
            print(print_str)

    @pytest.mark.parametrize('trickery', [0, 0.5, 1, 2])
    def test_print_trickery_vs_discipline(self, trickery):
        print(f" ~Discipline VS {trickery:0.1f} Trickery Across the Plate~")

        disciplines = [0, 0.5, 1, 2]

        print(f"Read chance at {trickery:0.1f} trickery, ({disciplines} discipline)")
        for i in range(0, 11):
            loc = 0.2 * i
            print_str = f"* {loc:0.1f} *  "
            for discipline in disciplines:
                obscurity = pitching.calc_obscurity(loc, trickery)
                read_chance = hitting.calc_read_chance(obscurity, discipline)
                print_str += f"{read_chance*100: >3.0f}%  "
            print(print_str)

    @pytest.mark.parametrize('swing_percent', [0, 0.1, 0.5, 0.9, 1])
    def test_roll_for_swing_decision(self, swing_percent, patcher):
        patcher.patch_normal('blaseball.playball.hitting.normal')
        swings = [hitting.roll_for_swing_decision(swing_percent) for __ in patcher]
        actual_percent = sum(swings) / 100
        assert actual_percent == pytest.approx(swing_percent, abs=0.05)  # rand_across_range includes outliers.

    # hit quality uses net contact: contact - pitch difficulty.
    # 0 force difficulty is about 0.3, 1 force difficulty is about 1.35.
    # net contact is thus 2 to about -3 for a far, far outside the plate 2 force.
    # 2 - (-2) is a wide range and 1 - (-1) is average.

    # MUST BE IN INCREASING ORDER:
    net_contacts = [-10, -4, -3, -1, -0.5, 0, 0.5, 0.8, 1, 2]

    @pytest.mark.parametrize('net_contact, previous_contact', zip(net_contacts[1:], net_contacts[:-1]))
    def test_roll_hit_quality(self, net_contact, previous_contact, patcher):
        patcher.patch_normal('blaseball.playball.hitting.normal')
        qualities = [hitting.roll_hit_quality(net_contact) for i in patcher]
        print(f" ~Hit Quality~")
        print(f"Net contact: {net_contact:0.1f}")
        average_hit_quality = statistics.mean(qualities)

        average_previous_quality = statistics.mean([hitting.roll_hit_quality(previous_contact) for i in patcher])
        assert average_hit_quality > average_previous_quality

        print(f"Average hit quality: {average_hit_quality:.2f}")

        min_hit_quality = min(qualities)
        max_hit_quality = max(qualities)

        assert min_hit_quality < 0
        assert max_hit_quality > 0
        print(f"Min: {min_hit_quality:.2f}, Max: {max_hit_quality:.2f}")

    def test_print_roll_hit_quality(self, patcher):
        patcher.patch_normal('blaseball.playball.hitting.normal')
        for net_contact in TestHitting.net_contacts[1:]:
            qualities = [hitting.roll_hit_quality(net_contact) for __ in patcher]

            strikes = sum([x <= 0 for x in qualities])
            fouls = sum([0 < x < 1 for x in qualities])
            fairs = sum([x >= 1 for x in qualities])
            print(f"* {net_contact:+0.1f} *  {strikes: >3} strikes, {fouls: >3} fouls, {fairs: >3} fair hits.")

    @pytest.mark.xfail
    def test_foul_rate(self, patcher):
        patcher.patch_normal('blaseball.playball.hitting.normal')
        qualities = [hitting.roll_hit_quality(-0.3) for __ in patcher]
        strikes = sum([x <= 0 for x in qualities])
        fouls = sum([0 < x < 1 for x in qualities])
        fairs = sum([x >= 1 for x in qualities])

        # MLB strike swinging percent: https://www.fantasypros.com/2020/02/sabermetrics-glossary-swinging-strike-rate/
        assert 10 < strikes < 20
        # foul percent: https://blogs.fangraphs.com/unpacking-the-impact-of-foul-balls-on-strikeouts/
        assert 25 < fouls < 50


class TestHitIntegrated:
    def test_print_pitch_fixture(self, pitch_1):
        # just a quickly accessible read on the default pitch
        print(pitch_1)

    def test_swing_results(self, pitch_1):
        pass

    def test_swing_stats_tracking(self, pitch_1, monkeypatch):
        pass