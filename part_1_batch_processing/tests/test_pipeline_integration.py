import pandas as pd

from pipeline.backup_validator import backup_validator
from pipeline.config import Config
from pipeline.processor import processor
from pipeline.reader import reader
from pipeline.validator import validator
from pipeline.writer import writer


def test_full_pipeline_runs_end_to_end(tmp_path, monkeypatch, row_factory):
    monkeypatch.setattr(Config, "LOCAL_OUTPUT_DIR", str(tmp_path))
    monkeypatch.setattr(Config, "OUTPUT_FILE", "processed_taxi_data.parquet")
    monkeypatch.setattr(Config, "AZURE_CONN_STRING", None)
    monkeypatch.setattr(Config, "AZURE_ACCOUNT_NAME", None)
    monkeypatch.setattr(Config, "AZURE_ACCOUNT_KEY", None)

    input_path = tmp_path / "sample_input.parquet"
    rows = [
        row_factory(),                              # valid
        row_factory(passenger_count=0),              # rejected at primary validation
        row_factory(trip_distance=-1),               # rejected at primary validation
    ]
    pd.DataFrame(rows).to_parquet(input_path, engine="pyarrow")

    raw_df = reader(str(input_path))
    assert len(raw_df) == 3

    validated_df, rejected_primary = validator(raw_df)
    assert len(validated_df) == 1
    assert len(rejected_primary) == 2

    processed_df = processor(validated_df)
    assert "trip_time_of_day" in processed_df.columns

    final_df, rejected_backup = backup_validator(processed_df)
    assert len(final_df) == 1
    assert len(rejected_backup) == 0

    result = writer(final_df, invalid_df=rejected_primary)

    output_path = tmp_path / "processed_taxi_data.parquet"
    assert output_path.exists()
    assert pd.read_parquet(output_path).shape[0] == 1
    assert "azure_url" not in result
