
import os
import uuid

import pandas as pd
import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt


def create_charts(file_path: str, numeric_columns: list) -> list:
    os.makedirs("charts", exist_ok=True)

    df = pd.read_csv(
        file_path,
        sep=None,
        engine="python",
        encoding="utf-8-sig"
    )

    columns = numeric_columns[:2]

    if not columns:
        return []

    fig, axes = plt.subplots(
        1,
        len(columns),
        figsize=(9 * len(columns), 5)
    )

    if len(columns) == 1:
        axes = [axes]

    for ax, column in zip(axes, columns):
        values = pd.to_numeric(
            df[column],
            errors="coerce"
        )

        valid_values = values.dropna()

        ax.plot(
            valid_values.index + 1,
            valid_values.values,
            marker="o",
            linewidth=2
        )

        ax.set_title(f"{column} - Data Trend")
        ax.set_xlabel("Row Number")
        ax.set_ylabel(column)
        ax.grid(True, alpha=0.3)

    fig.tight_layout()

    unique_id = uuid.uuid4().hex
    chart_path = f"charts/chart_{unique_id}.png"

    try:
        fig.savefig(chart_path, dpi=120)
    finally:
        plt.close(fig)

    return [chart_path]
