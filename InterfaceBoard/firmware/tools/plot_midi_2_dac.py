import csv
from matplotlib import pyplot as plt

dac_vals = []

with open("midi_2_dac.csv", "r") as f:
    reader = csv.reader(f)
    for row in reader:
        dac_vals.append(int(row[0]))

plt.plot(dac_vals)
plt.show()
