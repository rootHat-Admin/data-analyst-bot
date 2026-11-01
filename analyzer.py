
import pandas as pd


MAX_ROWS = 100_000
MAX_COLUMNS = 100
OUTLIER_SAMPLE_SIZE = 10
CALCULATION_TOLERANCE = 0.02


def analyze_csv(file_path: str) -> dict:

    header = pd.read_csv(
        file_path,
        sep=None,
        engine="python",
        encoding="utf-8-sig",
        nrows=0,
    )

    if len(header.columns) > MAX_COLUMNS:
        raise ValueError(
            f"CSV contains too many columns. "
            f"Maximum allowed: {MAX_COLUMNS}."
        )

    df = pd.read_csv(
        file_path,
        sep=None,
        engine="python",
        encoding="utf-8-sig",
        nrows=MAX_ROWS + 1,
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
            series = df[column].dropna()

            if not series.empty:
                column_stats.update({
                    "mean": float(series.mean()),
                    "median": float(series.median()),
                    "min": float(series.min()),
                    "max": float(series.max()),
                })

        statistics[column] = column_stats

    outliers = {}

    calculation_errors = {}

    def save_anomalies(column, mask, category):
        positions = mask[mask].index

        if len(positions) == 0:
            return

        sample = [
            {
                "row": int(index) + 2,
                "value": float(df.loc[index, column]),
            }
            for index in positions[:OUTLIER_SAMPLE_SIZE]
        ]

        outliers.setdefault(column, {
            "statistical": {
                "count": 0,
                "sample": [],
            },
            "business_rules": {
                "count": 0,
                "sample": [],
            },
        })

        outliers[column][category] = {
            "count": int(len(positions)),
            "sample": sample,
        }

    # ------------------------------------------
    # STATISTICAL OUTLIER DETECTION
    # ------------------------------------------

    rule_based_columns = {
        "customer_age",
        "quantity",
        "discount_percent",
        "delivery_days",
        "inventory_stock",
        "stock_quantity",
    }

    financial_columns = {
        "unit_price",
        "total_revenue",
        "cost_per_unit",
        "total_cost",
        "profit",
    }

    category_column = next(
        (
            column
            for column in df.columns
            if str(column).strip().lower()
            in {"product_category", "category"}
        ),
        None,
    )

    for column in numeric_columns:

        normalized_column = str(column).strip().lower()

        if normalized_column in rule_based_columns:
            continue

        series = df[column].dropna()

        if len(series) < 4:
            continue

        if (
            normalized_column in financial_columns
            and category_column is not None
        ):

            combined_mask = pd.Series(
                False,
                index=df.index,
            )

            grouped = df.groupby(
                category_column,
                dropna=True,
            )

            for _, group in grouped:
                group_series = group[column].dropna()

                if len(group_series) < 4:
                    continue

                q1 = group_series.quantile(0.25)
                q3 = group_series.quantile(0.75)
                iqr = q3 - q1

                if iqr == 0:
                    continue

                lower_bound = q1 - 1.5 * iqr
                upper_bound = q3 + 1.5 * iqr

                group_mask = (
                    (group[column] < lower_bound)
                    | (group[column] > upper_bound)
                ).fillna(False)

                combined_mask.loc[group.index] = group_mask

            mask = combined_mask

        else:
            q1 = series.quantile(0.25)
            q3 = series.quantile(0.75)
            iqr = q3 - q1

            if iqr == 0:
                continue

            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr

            mask = (
                (df[column] < lower_bound)
                | (df[column] > upper_bound)
            ).fillna(False)

        save_anomalies(
            column,
            mask,
            "statistical",
        )

    # ------------------------------------------
    # BUSINESS RULE VALIDATION
    # ------------------------------------------

    rules = {
        "customer_age": lambda s: (s < 18) | (s > 100),
        "unit_price": lambda s: s <= 0,
        "quantity": lambda s: (s <= 0) | (s > 100),
        "discount_percent": lambda s: (s < 0) | (s > 100),
        "total_revenue": lambda s: s < 0,
        "cost_per_unit": lambda s: s < 0,
        "total_cost": lambda s: s < 0,
        "delivery_days": lambda s: (s < 0) | (s > 30),
        "inventory_stock": lambda s: s < 0,
        "stock_quantity": lambda s: s < 0,
    }

    for column, rule in rules.items():

        if column not in df.columns:
            continue

        numeric_series = pd.to_numeric(
            df[column],
            errors="coerce",
        )

        mask = rule(numeric_series).fillna(False)

        save_anomalies(
            column,
            mask,
            "business_rules",
        )

    # ------------------------------------------
    # CALCULATION VALIDATION
    # ------------------------------------------

    def check_formula(name, expected):
        if name not in df.columns:
            return

        actual = pd.to_numeric(
            df[name],
            errors="coerce",
        )

        valid = actual.notna() & expected.notna()

        difference = (actual - expected).abs()

        mask = (
            valid
            & (difference > CALCULATION_TOLERANCE)
        ).fillna(False)

        positions = mask[mask].index

        if len(positions) == 0:
            return

        calculation_errors[name] = {
            "count": int(len(positions)),
            "sample": [
                {
                    "row": int(index) + 2,
                    "actual": float(actual.loc[index]),
                    "expected": float(expected.loc[index]),
                }
                for index in positions[:OUTLIER_SAMPLE_SIZE]
            ],
        }

    required_revenue = {
        "unit_price",
        "quantity",
        "discount_percent",
        "total_revenue",
    }

    if required_revenue.issubset(df.columns):

        expected_revenue = (
            df["unit_price"]
            * df["quantity"]
            * (1 - df["discount_percent"] / 100)
        )

        check_formula(
            "total_revenue",
            expected_revenue,
        )

    required_cost = {
        "cost_per_unit",
        "quantity",
        "total_cost",
    }

    if required_cost.issubset(df.columns):

        expected_cost = (
            df["cost_per_unit"]
            * df["quantity"]
        )

        check_formula(
            "total_cost",
            expected_cost,
        )

    required_profit = {
        "total_revenue",
        "total_cost",
        "profit",
    }

    if required_profit.issubset(df.columns):

        expected_profit = (
            df["total_revenue"]
            - df["total_cost"]
        )

        check_formula(
            "profit",
            expected_profit,
        )

    # ------------------------------------------
    # INSIGHTS
    # ------------------------------------------

    insights = []

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
        "calculation_errors": calculation_errors,
    }
