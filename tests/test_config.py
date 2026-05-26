import importlib
import os
from pathlib import Path
from unittest.mock import patch


@patch("app.config.Path.glob")
@patch("app.config.Path.exists")
def test_default_creds_file_uses_only_json_in_credentials_directory(
    mock_exists,
    mock_glob,
):
    creds_file = Path("credentials/service-account.json")
    mock_exists.return_value = False
    mock_glob.return_value = [creds_file]

    with patch.dict(os.environ, {}, clear=True):
        config = importlib.import_module("app.config")
        config = importlib.reload(config)

    assert config.GOOGLE_CREDS_FILE == str(creds_file)
