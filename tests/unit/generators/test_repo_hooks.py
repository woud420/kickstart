import os
from pathlib import Path
from unittest.mock import patch

from src.generators.service import ServiceGenerator
from src.generators.frontend import FrontendGenerator
from src.generators.lib import LibraryGenerator, CLIGenerator
from src.generators.monorepo import MonorepoGenerator


@patch('src.generators.service.create_repo')
def test_service_generator_calls_create_repo(mock_repo, tmp_path):
    gen = ServiceGenerator('svc', 'python', True, {}, root=tmp_path)
    gen.create()
    mock_repo.assert_called_once_with('svc')


@patch('src.generators.frontend.create_repo')
def test_frontend_generator_calls_create_repo(mock_repo, tmp_path):
    gen = FrontendGenerator('ui', True, {}, root=tmp_path)
    gen.create()
    mock_repo.assert_called_once_with('ui')


@patch('src.generators.lib.create_repo')
def test_lib_generator_calls_create_repo(mock_repo, tmp_path):
    gen = LibraryGenerator('lib', 'python', True, {}, root=tmp_path)
    gen.create()
    mock_repo.assert_called_once_with('lib')


@patch('src.generators.lib.create_repo')
def test_cli_generator_calls_create_repo(mock_repo, tmp_path):
    gen = CLIGenerator('cli', 'python', True, {}, root=tmp_path)
    gen.create()
    mock_repo.assert_called_once_with('cli')


@patch('src.generators.monorepo.create_repo')
def test_monorepo_generator_calls_create_repo(mock_repo, tmp_path):
    gen = MonorepoGenerator('mono', True, {}, root=tmp_path)
    gen.create()
    mock_repo.assert_called_once_with('mono')
