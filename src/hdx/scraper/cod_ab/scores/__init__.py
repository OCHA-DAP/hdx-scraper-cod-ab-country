from logging import getLogger
from pathlib import Path

from . import (
    geometry_topology,
    geometry_validity,
    output,
    table_areas,
    table_dates,
    table_languages,
    table_names,
    table_pcodes,
)
from hdx.scraper.cod_ab.utils import read_csv

logger = getLogger(__name__)


def main(iso3: str, data_dir: Path) -> float:
    """Applies scoring to the summarized values in "checks.csv".

    1. Create an iterable with each item containing the scoring function.

    2. Iterate through the score functions, generating a list of new DataFrames.

    3. After all the scoring has been performed, join the DataFrames together by ISO3
    and admin level.

    4. Output the final result to Excel: "saved_data/tables/cod_ab_data_quality.xlsx".
    """
    # NOTE: Register scores here.
    score_functions = (
        geometry_validity,
        geometry_topology,
        table_pcodes,
        table_names,
        table_languages,
        table_dates,
        table_areas,
    )
    checks_path = data_dir / iso3.lower() / f"{iso3.lower()}_checks.csv"
    if not checks_path.exists():
        return 0.0
    checks = read_csv(checks_path)
    score_results = []
    for function in score_functions:
        partial = function.main(checks)
        score_results.append(partial)
    output_table = None
    for partial in score_results:
        if output_table is None:
            output_table = partial
        else:
            output_table = output_table.merge(
                partial,
                on=["iso3", "level"],
                how="outer",
            )
    if output_table is not None:
        output_table_agg = output.main(iso3, output_table, data_dir)
        return output_table_agg["score"].iloc[0]
    return 0.0
