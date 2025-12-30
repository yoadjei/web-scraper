"""
Tests for the CLI.
"""

import pytest
from click.testing import CliRunner
from pathlib import Path

from webscraper.cli import main


class TestCLI:
    """Tests for CLI commands."""
    
    @pytest.fixture
    def runner(self):
        """Create a CLI runner."""
        return CliRunner()
    
    def test_version(self, runner):
        """Test version command."""
        result = runner.invoke(main, ["--version"])
        assert result.exit_code == 0
        assert "webscraper" in result.output
    
    def test_help(self, runner):
        """Test help command."""
        result = runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "run" in result.output
        assert "init" in result.output
        assert "validate" in result.output
    
    def test_init_command(self, runner, temp_dir):
        """Test init command creates config file."""
        config_path = temp_dir / "new_config.yaml"
        
        with runner.isolated_filesystem(temp_dir=str(temp_dir)):
            result = runner.invoke(main, ["init", str(config_path)])
            
            assert result.exit_code == 0
            assert config_path.exists()
            
            content = config_path.read_text()
            assert "base_url" in content
            assert "selectors" in content
    
    def test_validate_valid_config(self, runner, config_file):
        """Test validating a valid config."""
        result = runner.invoke(main, ["validate", str(config_file)])
        
        assert result.exit_code == 0
        assert "valid" in result.output.lower()
    
    def test_validate_missing_config(self, runner):
        """Test validating a non-existent config."""
        result = runner.invoke(main, ["validate", "nonexistent.yaml"])
        
        assert result.exit_code != 0
    
    def test_jobs_empty(self, runner, temp_dir):
        """Test jobs command with no saved jobs."""
        result = runner.invoke(main, ["jobs", "-d", str(temp_dir)])
        
        assert result.exit_code == 0
        assert "No saved jobs" in result.output
