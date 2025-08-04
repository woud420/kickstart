import os
from pathlib import Path
from unittest.mock import patch

from src.generator.service import ServiceGenerator
from src.generator.frontend import FrontendGenerator
from src.generator.lib import LibraryGenerator, CLIGenerator
from src.generator.monorepo import MonorepoGenerator


@patch('src.generator.service.create_repo')
def test_service_generator_calls_create_repo(mock_repo, tmp_path):
    gen = ServiceGenerator('svc', 'python', True, {}, root=tmp_path)
    gen.create()
    mock_repo.assert_called_once_with('svc')


@patch('src.generator.frontend.create_repo')
def test_frontend_generator_calls_create_repo(mock_repo, tmp_path):
    gen = FrontendGenerator('ui', True, {}, root=tmp_path)
    gen.create()
    mock_repo.assert_called_once_with('ui')


@patch('src.generator.lib.create_repo')
def test_lib_generator_calls_create_repo(mock_repo, tmp_path):
    gen = LibraryGenerator('lib', 'python', True, {}, root=tmp_path)
    gen.create()
    mock_repo.assert_called_once_with('lib')


@patch('src.generator.lib.create_repo')
def test_cli_generator_calls_create_repo(mock_repo, tmp_path):
    gen = CLIGenerator('cli', 'python', True, {}, root=tmp_path)
    gen.create()
    mock_repo.assert_called_once_with('cli')


@patch('src.generator.monorepo.create_repo')
def test_monorepo_generator_calls_create_repo(mock_repo, tmp_path):
    gen = MonorepoGenerator('mono', True, {}, root=tmp_path)
    gen.create()
    mock_repo.assert_called_once_with('mono')
