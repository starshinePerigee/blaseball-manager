from random import random


count = 0
total = 0

rolling_average = 0


NUMBER = 10000000  # 10 million


for i in range(NUMBER):
    r = random()

    count += 1
    total += r

    rolling_average -= rolling_average / count
    rolling_average += r / count


print(count)
print(total)
print(total / count)
print(rolling_average)

print("diff:" + str(total / count - rolling_average))
