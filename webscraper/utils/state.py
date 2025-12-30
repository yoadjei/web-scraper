"""
State management for resume capability.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, asdict

from webscraper.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class ScrapeState:
    """Represents the state of a scraping job."""
    
    job_id: str
    base_url: str
    started_at: str
    last_updated: str
    pages_scraped: int
    items_collected: int
    current_url: Optional[str]
    completed: bool
    urls_scraped: list[str]


class StateManager:
    """Manages scraping state for resume capability."""
    
    def __init__(self, checkpoint_dir: str = "./.scraper_state"):
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_state_path(self, job_id: str) -> Path:
        """Get the path to a state file."""
        return self.checkpoint_dir / f"{job_id}.json"
    
    def create_job(self, job_id: str, base_url: str) -> ScrapeState:
        """Create a new scraping job state."""
        now = datetime.utcnow().isoformat()
        state = ScrapeState(
            job_id=job_id,
            base_url=base_url,
            started_at=now,
            last_updated=now,
            pages_scraped=0,
            items_collected=0,
            current_url=base_url,
            completed=False,
            urls_scraped=[],
        )
        self.save_state(state)
        logger.info(f"Created job: {job_id}")
        return state
    
    def save_state(self, state: ScrapeState) -> None:
        """Save the current state to disk."""
        state.last_updated = datetime.utcnow().isoformat()
        state_path = self._get_state_path(state.job_id)
        
        with open(state_path, 'w') as f:
            json.dump(asdict(state), f, indent=2)
    
    def load_state(self, job_id: str) -> Optional[ScrapeState]:
        """Load a saved state from disk."""
        state_path = self._get_state_path(job_id)
        
        if not state_path.exists():
            return None
        
        try:
            with open(state_path, 'r') as f:
                data = json.load(f)
            return ScrapeState(**data)
        except (json.JSONDecodeError, TypeError) as e:
            logger.warning(f"Failed to load state for job {job_id}: {e}")
            return None
    
    def update_progress(
        self,
        state: ScrapeState,
        url: str,
        items_count: int,
    ) -> None:
        """Update the scraping progress."""
        state.pages_scraped += 1
        state.items_collected += items_count
        state.urls_scraped.append(url)
        state.current_url = url
        self.save_state(state)
    
    def mark_completed(self, state: ScrapeState) -> None:
        """Mark the job as completed."""
        state.completed = True
        state.current_url = None
        self.save_state(state)
        logger.info(f"Job {state.job_id} completed: {state.items_collected} items from {state.pages_scraped} pages")
    
    def list_jobs(self) -> list[ScrapeState]:
        """List all saved jobs."""
        jobs = []
        for state_file in self.checkpoint_dir.glob("*.json"):
            state = self.load_state(state_file.stem)
            if state:
                jobs.append(state)
        return jobs
    
    def delete_job(self, job_id: str) -> bool:
        """Delete a saved job state."""
        state_path = self._get_state_path(job_id)
        if state_path.exists():
            state_path.unlink()
            logger.info(f"Deleted job: {job_id}")
            return True
        return False
    
    def get_resumable_url(self, state: ScrapeState) -> Optional[str]:
        """Get the URL to resume from."""
        if state.completed:
            return None
        return state.current_url
