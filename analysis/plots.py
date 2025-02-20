import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

from utils.load_save_functions import load_settings
from utils.logger import Logger


class Plotter:

    def __init__(self):
        self.df = None
        self.settings = load_settings()
        self.fontsize_labels = 15
        self.window_size = 20
        self.logger = Logger(
            name="protocol",
            file_path=f'experiments/{self.settings["EXPERIMENT_NAME"]}/meta_data',
        )

    def _load_data(self, df: pd.DataFrame):
        self.df = df

    def _smooth_data(self, x: list):
        x_smooth = np.convolve(x, np.ones(self.window_size), "valid") / self.window_size
        return x_smooth

    def plot_results_well_id(self, df: pd.DataFrame):
        try:
            self._load_data(df)

            wells_ids = self.df["well id"]
            st_eq = self.df["surface tension eq. (mN/m)"]

            plt.figure(figsize=(10, 6))
            plt.bar(wells_ids, st_eq, color="C0")
            plt.xlabel("Well ID", fontsize=self.fontsize_labels)
            plt.ylabel("Surface Tension Eq. (mN/m)", fontsize=self.fontsize_labels)
            plt.title(
                f"Results experiment {self.settings['EXPERIMENT_NAME']}",
                fontsize=1.5 * self.fontsize_labels,
            )
            plt.xticks(rotation=45, ha="right")
            plt.tight_layout()

            # save in experiment folder and plots cache for web interface
            plt.savefig(f"experiments/{self.settings['EXPERIMENT_NAME']}/results_plot.png")
            plt.savefig("server/static/plots_cache/results_plot.png")

            self.logger.info("Plotter: created results plot with well IDs.")
        except Exception as e:
            self.logger.warning(f"Plotter: could not create plot results with well IDs. Error: {e}")

    def plot_dynamic_surface_tension(self, df: pd.DataFrame, well_id: str):
        try:
            self._load_data(df)

            t = self.df["time (s)"]
            st = self.df["surface tension (mN/m)"]

            t_smooth = self._smooth_data(t)
            st_smooth = self._smooth_data(st)

            fig, ax = plt.subplots()
            ax.plot(t_smooth, st_smooth, lw=2, color="black")
            ax.set_xlim(0, t_smooth[-1] + 5)
            ax.set_ylim(20, 80)
            ax.set_xlabel("Time (s)", fontsize=self.fontsize_labels)
            ax.set_ylabel("Surface Tension (mN/m)", fontsize=self.fontsize_labels)
            ax.set_title(f"Well ID: {well_id}")
            ax.grid(axis="y")

            plt.savefig(f"experiments/{self.settings['EXPERIMENT_NAME']}/data/{well_id}/dynamic_surface_tension_plot.png")
            plt.savefig("server/static/plots_cache/dynamic_surface_tension_plot.png")
            self.logger.info("Plotter: dynamic surface tension plot created.")
        except Exception as e:
            self.logger.warning(f"Plotter: could not create dynamic surface tension plot. Error: {e}")

    def plot_results_concentration(self):
        pass
