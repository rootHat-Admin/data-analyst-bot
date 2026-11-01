import pandas as pd


MAX_ROWS = 100_000
MAX_COLUMNS = 100
OUTLIER_SAMPLE_SIZE = 10


def analyze_csv(file_path: str) -> dict:

    # Check the number of columns before loading the full dataset.
    header = pd.read_csv(
        file_path,
        sep=None,
        engine="python",
        encoding="utf-8-sig",
        nrows=0
    )

    if len(header.columns) > MAX_COLUMNS:
        raise ValueError(
            f"CSV contains too many columns. "
            f"Maximum allowed: {MAX_COLUMNS}."
        )

    # Read only one row above the limit to detect oversized files.
    df = pd.read_csv(
        file_path,
        sep=None,
        engine="python",
        encoding="utf-8-sig",
        nrows=MAX_ROWS + 1
    )

    if df.empty:
        raise ValueError("The CSV file is empty.")

    if len(df) > MAX_ROWS:
        raise ValueError(
            f"CSV contains too many rows. "
            f"Maximum allowed: {MAX_ROWS}."
        )

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

        if len(unusual_values) == 0:
            continue

        # Keep the row index for each outlier so the exact
        # record can be located in the original CSV.
        sample_pairs = [
            {"row": int(index) + 1, "value": float(value)}
            for index, value in unusual_values.head(
                OUTLIER_SAMPLE_SIZE
            ).items()
        ]

        outliers[column] = {
            "count": int(len(unusual_values)),
            "sample": sample_pairs,
        }

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
                f"{column}: the last observed value was "
                f"{change:.2f}% different from the first observed value. "
                "This comparison does not necessarily indicate a trend."
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