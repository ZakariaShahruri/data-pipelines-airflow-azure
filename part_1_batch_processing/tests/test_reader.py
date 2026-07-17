import pandas as pd
import pytest

from pipeline.reader import reader


def test_exits_when_file_missing(tmp_path):
    with pytest.raises(SystemExit):
        reader(str(tmp_path / "does_not_exist.parquet"))


def test_reads_valid_parquet_file(tmp_path):
    path = tmp_path / "sample.parquet"
    pd.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]}).to_parquet(path, engine="pyarrow")

    df = reader(str(path))
    assert len(df) == 3
    assert list(df.columns) == ["a", "b"]


def test_exits_on_empty_file(tmp_path):
    path = tmp_path / "empty.parquet"
    pd.DataFrame({"a": []}).to_parquet(path, engine="pyarrow")

    with pytest.raises(SystemExit):
        reader(str(path))
