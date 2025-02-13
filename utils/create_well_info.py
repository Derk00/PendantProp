import pandas as pd
import numpy as np

letters = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']
numbers = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
wells = []
for number in numbers:
    for letter in letters:
        wells.append(letter + str(number))

location = 6 * np.ones(len(wells), dtype=int)
description = ['water'] * len(wells)

# create dataframe with headers 'location', 'well', 'description'
well_info = pd.DataFrame({'location': location, 'well': wells, 'description': description})
well_info.to_csv('well_info_justin.csv', index=False)
# print(well_info)