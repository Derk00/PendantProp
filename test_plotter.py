from analysis.plots import Plotter
import pandas as pd

df = pd.read_csv("results.csv")
plotter = Plotter()
plotter.plot_results_well_id(df=df)
