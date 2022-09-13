from prototypes import protostatsource as ps

print(ps.stat_one)  # y

print(ps.stat_dict['stat_two'])  # n
print(ps.stat_dict['stat_three'])  # n

print(ps.StatClass.stat_four)  # y

print(ps.stat_class.stat_four)  # y
print(ps.stat_class.stat_five)  # y

print(ps.stat_class.stat_six)  # n
