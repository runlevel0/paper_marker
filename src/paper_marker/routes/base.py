from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from paper_marker.core.models import CandidateResult


class ConversionRoute(ABC):
    name: str

    @abstractmethod
    def is_available(self) -> tuple[bool, str]:
        """Return route availability and optional note."""

    @abstractmethod
    def convert(self, pdf_path: Path, work_dir: Path, timeout_s: int) -> CandidateResult:
        """Convert the PDF and return a candidate result."""
