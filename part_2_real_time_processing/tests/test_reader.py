import pandas as pd
import pytest

from pipeline.config import Config
from pipeline.reader import load_data


@pytest.fixture(autouse=True)
def _isolate_input_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(Config, "INPUT_DIR", tmp_path)
    return tmp_path


def test_raises_when_file_missing(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_data("does_not_exist.csv")


def test_reads_csv_file(tmp_path):
    pd.DataFrame({"a": [1, 2], "b": ["x", "y"]}).to_csv(tmp_path / "data.csv", index=False)
    df = load_data("data.csv")
    assert len(df) == 2
    assert list(df.columns) == ["a", "b"]


def test_reads_xlsx_file(tmp_path):
    pd.DataFrame({"a": [1, 2], "b": ["x", "y"]}).to_excel(tmp_path / "data.xlsx", index=False)
    df = load_data("data.xlsx")
    assert len(df) == 2


def test_returns_empty_df_when_file_has_no_rows(tmp_path):
    pd.DataFrame({"a": []}).to_csv(tmp_path / "empty.csv", index=False)
    df = load_data("empty.csv")
    assert df.empty
