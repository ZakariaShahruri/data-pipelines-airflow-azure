from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from pipeline.config import Config
from pipeline.writer import writer


@pytest.fixture
def sample_df():
    return pd.DataFrame({"total_amount": [10.0, 20.0]})


@pytest.fixture(autouse=True)
def _isolate_output_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(Config, "LOCAL_OUTPUT_DIR", str(tmp_path))
    monkeypatch.setattr(Config, "OUTPUT_FILE", "processed.parquet")
    monkeypatch.setattr(Config, "AZURE_CONN_STRING", None)
    monkeypatch.setattr(Config, "AZURE_ACCOUNT_NAME", None)
    monkeypatch.setattr(Config, "AZURE_ACCOUNT_KEY", None)
    return tmp_path


def test_writes_valid_rows_locally(sample_df, tmp_path):
    result = writer(sample_df)
    out_path = tmp_path / "processed.parquet"
    assert out_path.exists()
    assert result["local_valid"] == out_path
    assert pd.read_parquet(out_path).equals(sample_df)


def test_writes_invalid_rows_locally_when_provided(sample_df, tmp_path):
    invalid_df = pd.DataFrame({"total_amount": [-1.0]})
    result = writer(sample_df, invalid_df=invalid_df)
    assert (tmp_path / "rejected_rows.parquet").exists()
    assert result["local_invalid"] == tmp_path / "rejected_rows.parquet"


def test_skips_azure_upload_when_no_credentials(sample_df):
    result = writer(sample_df)
    assert "azure_url" not in result


def test_uploads_to_azure_when_credentials_present(sample_df, monkeypatch):
    monkeypatch.setattr(Config, "AZURE_CONN_STRING", "fake-connection-string")

    mock_blob_client = MagicMock()
    mock_blob_client.url = "https://fakestorage.blob.core.windows.net/taxiproject/processed.parquet"

    mock_container_client = MagicMock()
    mock_container_client.get_blob_client.return_value = mock_blob_client

    mock_service = MagicMock()
    mock_service.get_container_client.return_value = mock_container_client

    with patch("pipeline.writer.BlobServiceClient") as mock_blob_service_cls:
        mock_blob_service_cls.from_connection_string.return_value = mock_service
        result = writer(sample_df)

    mock_blob_client.upload_blob.assert_called_once()
    assert result["azure_url"] == mock_blob_client.url


def test_azure_failure_does_not_raise_and_keeps_local_result(sample_df, monkeypatch):
    monkeypatch.setattr(Config, "AZURE_CONN_STRING", "fake-connection-string")

    with patch("pipeline.writer.BlobServiceClient") as mock_blob_service_cls:
        mock_blob_service_cls.from_connection_string.side_effect = RuntimeError("network down")
        result = writer(sample_df)

    assert "azure_url" not in result
    assert "local_valid" in result
