"""
Base exporter class.
"""

from abc import ABC, abstractmethod
from typing import Any


class BaseExporter(ABC):
    """Abstract base class for data exporters."""
    
    @abstractmethod
    async def export(self, data: list[dict[str, Any]], path: str) -> None:
        """
        Export data to a destination.
        
        Args:
            data: List of data dictionaries
            path: Output path or destination
        """
        pass
    
    @abstractmethod
    def get_extension(self) -> str:
        """Get the file extension for this exporter."""
        pass
