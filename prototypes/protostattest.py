from prototypes import protostatsource as ps

print(ps.stat_one)  # y

print(ps.stat_dict['stat_two'])  # n
print(ps.stat_dict['stat_three'])  # n

print(ps.StatClass.stat_four)  # y

print(ps.stat_class.stat_four)  # y
print(ps.stat_class.stat_five)  # y

print(ps.stat_class.stat_six)  # n

print(ps.stat_seven)  # y
print(ps.stat_eight)  # y

sc = ps.StatClass()

print(sc.stat_four)  # y
print(sc.stat_five)  # y
print(sc.stat_six)  # broke lol

# from blaseball.stats import stats as s
# print(s.name)  # does suggest