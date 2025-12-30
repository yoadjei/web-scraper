"""
Rich-based logging utilities.
"""

import logging
from typing import Optional

from rich.console import Console
from rich.logging import RichHandler
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeElapsedColumn


# Global console instance
console = Console()

# Logger cache
_loggers: dict[str, logging.Logger] = {}


def setup_logging(level: str = "INFO", verbose: bool = False) -> None:
    """Set up logging with Rich handler."""
    log_level = getattr(logging, level.upper(), logging.INFO)
    
    # Configure root logger
    logging.basicConfig(
        level=log_level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[
            RichHandler(
                console=console,
                rich_tracebacks=True,
                show_path=verbose,
                show_time=True,
            )
        ],
    )


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance by name."""
    if name not in _loggers:
        _loggers[name] = logging.getLogger(name)
    return _loggers[name]


def create_progress() -> Progress:
    """Create a Rich progress bar for scraping."""
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        TimeElapsedColumn(),
        console=console,
    )


def print_success(message: str) -> None:
    """Print a success message."""
    console.print(f"[bold green]✓[/] {message}")


def print_error(message: str) -> None:
    """Print an error message."""
    console.print(f"[bold red]✗[/] {message}")


def print_warning(message: str) -> None:
    """Print a warning message."""
    console.print(f"[bold yellow]![/] {message}")


def print_info(message: str) -> None:
    """Print an info message."""
    console.print(f"[bold blue]ℹ[/] {message}")
