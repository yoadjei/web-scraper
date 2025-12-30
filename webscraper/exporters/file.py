"""
File-based exporters for CSV, JSON, and Parquet formats.
"""

import asyncio
from pathlib import Path
from typing import Any, Literal

import pandas as pd

from webscraper.exporters.base import BaseExporter
from webscraper.utils.logging import get_logger, print_success

logger = get_logger(__name__)


class FileExporter(BaseExporter):
    """Export data to various file formats."""
    
    def __init__(self, format: Literal["csv", "json", "parquet"] = "csv"):
        self.format = format
    
    def get_extension(self) -> str:
        """Get file extension for the format."""
        return f".{self.format}"
    
    async def export(self, data: list[dict[str, Any]], path: str) -> None:
        """
        Export data to a file.
        
        Args:
            data: List of data dictionaries
            path: Output path (without extension)
        """
        if not data:
            logger.warning("No data to export")
            return
        
        # Ensure output directory exists
        output_path = Path(path).with_suffix(self.get_extension())
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Run sync export in thread pool
        await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: self._export_sync(data, output_path)
        )
        
        print_success(f"Exported {len(data)} items to {output_path}")
    
    def _export_sync(self, data: list[dict[str, Any]], path: Path) -> None:
        """Synchronous export implementation."""
        df = pd.DataFrame(data)
        
        if self.format == "csv":
            df.to_csv(path, index=False, encoding="utf-8")
        elif self.format == "json":
            df.to_json(path, orient="records", indent=2, force_ascii=False)
        elif self.format == "parquet":
            df.to_parquet(path, index=False)
        else:
            raise ValueError(f"Unsupported format: {self.format}")


class CSVExporter(FileExporter):
    """Export to CSV format."""
    
    def __init__(self):
        super().__init__(format="csv")


class JSONExporter(FileExporter):
    """Export to JSON format."""
    
    def __init__(self):
        super().__init__(format="json")


class ParquetExporter(FileExporter):
    """Export to Parquet format."""
    
    def __init__(self):
        super().__init__(format="parquet")
