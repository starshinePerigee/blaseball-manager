import pandas as pd


print("should raise fragmentation warning twice")

df1 = pd.DataFrame()

for i in range(102):
    df1[f"col{i}"] = 0

# should not raise fragmentation warning:

df2 = pd.DataFrame()

cols = [f"col{i+200}" for i in range(102)]

df2 = pd.DataFrame(columns=cols)

df3 = pd.concat([df1, df2])
print(df3)
