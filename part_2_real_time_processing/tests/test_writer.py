from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from pipeline.config import Config
from pipeline.writer import write_data


@pytest.fixture
def sample_df():
    return pd.DataFrame({"Total Spent": [10.0, 20.0]})


@pytest.fixture(autouse=True)
def _isolate_output_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(Config, "OUTPUT_DIR", tmp_path)
    monkeypatch.setattr(Config, "AZURE_CONN_STRING", None)
    return tmp_path


def test_writes_csv_locally(sample_df, tmp_path):
    write_data(sample_df, "processed.csv")
    out_path = tmp_path / "processed.csv"
    assert out_path.exists()
    assert len(pd.read_csv(out_path)) == 2


def test_skips_azure_upload_when_no_credentials(sample_df, tmp_path, caplog):
    write_data(sample_df, "processed.csv")
    assert (tmp_path / "processed.csv").exists()


def test_uploads_to_azure_when_credentials_present(sample_df, monkeypatch):
    monkeypatch.setattr(Config, "AZURE_CONN_STRING", "fake-connection-string")

    mock_blob_client = MagicMock()
    mock_blob_client.url = "https://fakestorage.blob.core.windows.net/inventory-output/processed.csv"

    mock_container_client = MagicMock()
    mock_container_client.get_blob_client.return_value = mock_blob_client

    mock_service = MagicMock()
    mock_service.get_container_client.return_value = mock_container_client

    with patch("pipeline.writer.BlobServiceClient") as mock_blob_service_cls:
        mock_blob_service_cls.from_connection_string.return_value = mock_service
        write_data(sample_df, "processed.csv")

    mock_blob_client.upload_blob.assert_called_once()


def test_azure_failure_does_not_raise(sample_df, monkeypatch):
    monkeypatch.setattr(Config, "AZURE_CONN_STRING", "fake-connection-string")

    with patch("pipeline.writer.BlobServiceClient") as mock_blob_service_cls:
        mock_blob_service_cls.from_connection_string.side_effect = RuntimeError("network down")
        write_data(sample_df, "processed.csv")  # must not raise
