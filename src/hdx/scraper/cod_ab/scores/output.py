from pathlib import Path

from pandas import DataFrame


def aggregate(checks: DataFrame) -> DataFrame:
    """Summarize scores by averaging scores from each admin level.

    Args:
        checks: Resulting DataFrame created by scoring functions.

    Returns:
        Dataframe grouped and averaged by ISO3.
    """
    checks = checks.drop(columns=["level"])
    checks = checks.groupby("iso3").mean()
    checks["score"] = checks.mean(axis=1)
    checks = checks.round(3)
    return checks.sort_values(by=["score", "iso3"])


def main(iso3: str, checks: DataFrame, data_dir: Path) -> DataFrame:
    """Aggregates scores and outputs to an Excel workbook with red/amber/green coloring.

    1. Groups and averages the scores generated in this module and outputs as a CSV.

    2. Applied styling to the dataset generated in step 1 and saves as Excel.

    3. Adds all CSVs generated in previous modules to the Excel workbook.

    4. Adds a final sheet specifying which date the workbook was generated on.

    Args:
        iso3: ISO# string.
        metadata: metadata DataFrame.
        checks: checks DataFrame.
    """
    scores = aggregate(checks)
    scores.to_csv(
        data_dir / iso3.lower() / f"{iso3.lower()}_scores.csv",
        encoding="utf-8-sig",
    )
    return scores
