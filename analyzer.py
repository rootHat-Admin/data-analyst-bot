
import pandas as pd


def analyze_csv(file_path: str) -> dict:
    df = pd.read_csv(
        file_path,
        sep=None,
        engine="python",
        encoding="utf-8-sig"
    )

    if df.empty:
        raise ValueError("The CSV file is empty.")

    missing_values = int(df.isna().sum().sum())
    duplicate_rows = int(df.duplicated().sum())

    numeric_columns = df.select_dtypes(
        include="number"
    ).columns.tolist()

    statistics = {}

    for column in df.columns:
        missing = int(df[column].isna().sum())

        column_stats = {
            "missing": missing,
            "unique": int(df[column].nunique()),
        }

        if column in numeric_columns:
            column_stats.update({
                "mean": float(df[column].mean()),
                "median": float(df[column].median()),
                "min": float(df[column].min()),
                "max": float(df[column].max()),
            })

        statistics[column] = column_stats

    outliers = {}

    for column in numeric_columns:
        series = df[column].dropna()

        if len(series) < 4:
            continue

        Q1 = series.quantile(0.25)
        Q3 = series.quantile(0.75)

        IQR = Q3 - Q1

        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR

        unusual_values = series[
            (series < lower_bound) |
            (series > upper_bound)
        ]

        outliers[column] = unusual_values.tolist()

    insights = []

    for column in numeric_columns:
        series = df[column].dropna()

        if len(series) < 2:
            continue

        first = series.iloc[0]
        last = series.iloc[-1]

        if first != 0:
            change = ((last - first) / abs(first)) * 100

            insights.append(
                f"{column}: changed by {change:.2f}% "
                "from the first to the last observation."
            )

    return {
        "rows": len(df),
        "columns": len(df.columns),
        "numeric_columns": numeric_columns,
        "statistics": statistics,
        "insights": insights,
        "data_quality": {
            "missing_values": missing_values,
            "duplicate_rows": duplicate_rows,
        },
        "outliers": outliers,
    }
