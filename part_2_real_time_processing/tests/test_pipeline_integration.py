import pandas as pd

from pipeline.backup_validator import backup_validate
from pipeline.config import Config
from pipeline.processor import process_data
from pipeline.reader import load_data
from pipeline.validator import validate_data
from pipeline.writer import write_data


def test_full_pipeline_runs_end_to_end(tmp_path, monkeypatch, row_factory):
    monkeypatch.setattr(Config, "INPUT_DIR", tmp_path)
    monkeypatch.setattr(Config, "OUTPUT_DIR", tmp_path)
    monkeypatch.setattr(Config, "AZURE_CONN_STRING", None)

    rows = [
        row_factory(),                                            # valid
        row_factory(**{"Customer ID": None}),                     # dropped: missing customer id
    ]
    pd.DataFrame(rows).to_csv(tmp_path / "inventory.csv", index=False)

    raw_df = load_data("inventory.csv")
    assert len(raw_df) == 2

    validated_df = validate_data(raw_df)
    assert len(validated_df) == 1

    processed_df = process_data(validated_df)
    assert "Vat_Amount" in processed_df.columns

    final_df = backup_validate(processed_df)
    assert len(final_df) == 1

    write_data(final_df, "inventory_processed.csv")
    output_path = tmp_path / "inventory_processed.csv"
    assert output_path.exists()
    assert len(pd.read_csv(output_path)) == 1
