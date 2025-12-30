"""
Tests for exporters.
"""

import pytest
import json
import pandas as pd
from pathlib import Path

from webscraper.exporters.file import FileExporter, CSVExporter, JSONExporter, ParquetExporter


class TestFileExporter:
    """Tests for file exporters."""
    
    @pytest.fixture
    def sample_data(self):
        """Sample data for export tests."""
        return [
            {"title": "Product One", "price": "£10.00"},
            {"title": "Product Two", "price": "£20.00"},
            {"title": "Product Three", "price": "£30.00"},
        ]
    
    @pytest.mark.asyncio
    async def test_csv_export(self, sample_data, temp_dir):
        """Test CSV export."""
        exporter = CSVExporter()
        output_path = temp_dir / "output"
        
        await exporter.export(sample_data, str(output_path))
        
        csv_file = output_path.with_suffix(".csv")
        assert csv_file.exists()
        
        df = pd.read_csv(csv_file)
        assert len(df) == 3
        assert list(df.columns) == ["title", "price"]
    
    @pytest.mark.asyncio
    async def test_json_export(self, sample_data, temp_dir):
        """Test JSON export."""
        exporter = JSONExporter()
        output_path = temp_dir / "output"
        
        await exporter.export(sample_data, str(output_path))
        
        json_file = output_path.with_suffix(".json")
        assert json_file.exists()
        
        with open(json_file) as f:
            data = json.load(f)
        
        assert len(data) == 3
        assert data[0]["title"] == "Product One"
    
    @pytest.mark.asyncio
    async def test_parquet_export(self, sample_data, temp_dir):
        """Test Parquet export."""
        exporter = ParquetExporter()
        output_path = temp_dir / "output"
        
        await exporter.export(sample_data, str(output_path))
        
        parquet_file = output_path.with_suffix(".parquet")
        assert parquet_file.exists()
        
        df = pd.read_parquet(parquet_file)
        assert len(df) == 3
    
    @pytest.mark.asyncio
    async def test_empty_data_export(self, temp_dir):
        """Test exporting empty data."""
        exporter = CSVExporter()
        output_path = temp_dir / "empty_output"
        
        await exporter.export([], str(output_path))
        
        # Should not create file for empty data
        csv_file = output_path.with_suffix(".csv")
        assert not csv_file.exists()
    
    def test_get_extension(self):
        """Test file extension methods."""
        assert CSVExporter().get_extension() == ".csv"
        assert JSONExporter().get_extension() == ".json"
        assert ParquetExporter().get_extension() == ".parquet"
