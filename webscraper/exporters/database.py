"""
Database exporters for SQLite and PostgreSQL.
"""

import asyncio
from typing import Any, Literal, Optional

import pandas as pd

from webscraper.exporters.base import BaseExporter
from webscraper.utils.logging import get_logger, print_success

logger = get_logger(__name__)

# Lazy check for SQLAlchemy
_sqlalchemy_available = None


def _check_sqlalchemy() -> bool:
    """Check if SQLAlchemy is available."""
    global _sqlalchemy_available
    if _sqlalchemy_available is None:
        try:
            import sqlalchemy
            _sqlalchemy_available = True
        except ImportError:
            _sqlalchemy_available = False
    return _sqlalchemy_available


class DatabaseExporter(BaseExporter):
    """Export data to SQL databases."""
    
    def __init__(
        self,
        connection_string: str,
        table_name: str = "scraped_data",
        if_exists: Literal["replace", "append", "fail"] = "append",
    ):
        """
        Initialize database exporter.
        
        Args:
            connection_string: SQLAlchemy connection string
            table_name: Target table name
            if_exists: What to do if table exists ('replace', 'append', 'fail')
        """
        if not _check_sqlalchemy():
            raise ImportError(
                "SQLAlchemy is required for database export. "
                "Install it with: pip install 'webscraper[database]'"
            )
        
        self.connection_string = connection_string
        self.table_name = table_name
        self.if_exists = if_exists
    
    def get_extension(self) -> str:
        """Database exports don't have file extensions."""
        return ""
    
    async def export(self, data: list[dict[str, Any]], path: str = "") -> None:
        """
        Export data to a database table.
        
        Args:
            data: List of data dictionaries
            path: Ignored for database exports
        """
        if not data:
            logger.warning("No data to export")
            return
        
        # Run sync export in thread pool
        await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: self._export_sync(data)
        )
        
        print_success(f"Exported {len(data)} items to table '{self.table_name}'")
    
    def _export_sync(self, data: list[dict[str, Any]]) -> None:
        """Synchronous export implementation."""
        from sqlalchemy import create_engine
        
        engine = create_engine(self.connection_string)
        df = pd.DataFrame(data)
        
        df.to_sql(
            self.table_name,
            engine,
            if_exists=self.if_exists,
            index=False,
        )
        
        engine.dispose()


class SQLiteExporter(DatabaseExporter):
    """Export to SQLite database."""
    
    def __init__(
        self,
        db_path: str = "./output/scraped_data.db",
        table_name: str = "scraped_data",
        if_exists: Literal["replace", "append", "fail"] = "append",
    ):
        connection_string = f"sqlite:///{db_path}"
        super().__init__(connection_string, table_name, if_exists)


class PostgreSQLExporter(DatabaseExporter):
    """Export to PostgreSQL database."""
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 5432,
        database: str = "webscraper",
        username: str = "postgres",
        password: str = "",
        table_name: str = "scraped_data",
        if_exists: Literal["replace", "append", "fail"] = "append",
    ):
        connection_string = f"postgresql://{username}:{password}@{host}:{port}/{database}"
        super().__init__(connection_string, table_name, if_exists)
