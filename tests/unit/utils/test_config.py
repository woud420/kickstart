import pytest
from pathlib import Path
from unittest.mock import patch, mock_open
import toml
from src.utils.config import load_config

@pytest.fixture
def mock_config_data():
    return {
        "key1": "value1",
        "key2": "value2"
    }

def test_load_config_from_cwd(tmp_path, mock_config_data):
    config_path = tmp_path / ".kickstart.toml"
    config_path.write_text(toml.dumps(mock_config_data))
    
    with patch('pathlib.Path.cwd', return_value=tmp_path):
        config = load_config()
        assert config == mock_config_data

def test_load_config_from_home(tmp_path, mock_config_data):
    home_config = tmp_path / ".kickstartrc"
    home_config.write_text(toml.dumps(mock_config_data))
    
    with patch('pathlib.Path.home', return_value=tmp_path):
        config = load_config()
        assert config == mock_config_data

def test_load_config_from_config_dir(tmp_path, mock_config_data):
    config_dir = tmp_path / ".config" / "kickstart"
    config_dir.mkdir(parents=True)
    config_file = config_dir / "config.toml"
    config_file.write_text(toml.dumps(mock_config_data))
    
    with patch('pathlib.Path.home', return_value=tmp_path):
        config = load_config()
        assert config == mock_config_data

def test_load_config_merges_multiple_files(tmp_path):
    cwd_config = {"key1": "value1"}
    home_config = {"key2": "value2"}
    config_dir_config = {"key3": "value3"}
    
    (tmp_path / ".kickstart.toml").write_text(toml.dumps(cwd_config))
    (tmp_path / ".kickstartrc").write_text(toml.dumps(home_config))
    config_dir = tmp_path / ".config" / "kickstart"
    config_dir.mkdir(parents=True)
    (config_dir / "config.toml").write_text(toml.dumps(config_dir_config))
    
    with patch('pathlib.Path.cwd', return_value=tmp_path), \
         patch('pathlib.Path.home', return_value=tmp_path):
        config = load_config()
        assert config == {**cwd_config, **home_config, **config_dir_config}

def test_load_config_no_files():
    with patch('pathlib.Path.exists', return_value=False):
        config = load_config()
        assert config == {} 
