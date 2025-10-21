"""MCP Developer Diary for validation quality tracking.

This module centralises diary entries for MCP-based validators to ensure
quality, correctness monitoring, and knowledge retention. It persists entries
as JSON and tracks the strongest researched quality standard so that newer
standards only replace the current benchmark when they achieve a higher score.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class DiaryEntry:
    """Single diary entry capturing validation context and decisions."""

    entry_id: str
    timestamp_utc: str
    component: str
    summary: str
    quality_metrics: Dict[str, float]
    validation_outcome: str
    research_sources: List[str] = field(default_factory=list)
    lessons_learned: List[str] = field(default_factory=list)
    global_actions: List[str] = field(default_factory=list)
    proposed_standard: str = ""
    proposed_standard_score: Optional[float] = None
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    supersedes: Optional[str] = None
    superseded_by: Optional[str] = None
    is_current_best_standard: bool = False


class MCPDeveloperDiary:
    """Persistent developer diary tailored for MCP validation workflows."""

    def __init__(self, storage_path: Optional[Path] = None, max_entries: int = 750):
        self.storage_path = storage_path or Path(__file__).resolve().parent / "mcp_developer_diary.json"
        self.max_entries = max_entries
        self.entries: List[DiaryEntry] = []
        self.best_standard_entry_id: Optional[str] = None
        self._load()

    # ------------------------------------------------------------------
    # Persistence helpers
    # ------------------------------------------------------------------
    def _load(self) -> None:
        if not self.storage_path.exists():
            return

        try:
            raw = json.loads(self.storage_path.read_text(encoding="utf-8"))
            raw_entries = raw.get("entries", [])
            self.best_standard_entry_id = raw.get("best_standard_entry_id")

            for payload in raw_entries:
                entry = DiaryEntry(
                    entry_id=payload.get("entry_id", ""),
                    timestamp_utc=payload.get("timestamp_utc", ""),
                    component=payload.get("component", ""),
                    summary=payload.get("summary", ""),
                    quality_metrics=payload.get("quality_metrics", {}),
                    validation_outcome=payload.get("validation_outcome", ""),
                    research_sources=payload.get("research_sources", []),
                    lessons_learned=payload.get("lessons_learned", []),
                    global_actions=payload.get("global_actions", []),
                    proposed_standard=payload.get("proposed_standard", ""),
                    proposed_standard_score=payload.get("proposed_standard_score"),
                    tags=payload.get("tags", []),
                    metadata=payload.get("metadata", {}),
                    supersedes=payload.get("supersedes"),
                    superseded_by=payload.get("superseded_by"),
                    is_current_best_standard=payload.get("is_current_best_standard", False),
                )
                self.entries.append(entry)

            # Rebuild best standard pointer if missing or corrupt
            if self.best_standard_entry_id and not self._find_entry(self.best_standard_entry_id):
                self.best_standard_entry_id = None
            if self.best_standard_entry_id is None:
                self._recalculate_best_standard()
        except Exception:
            # On corrupted file we start fresh but keep original as backup
            backup_path = self.storage_path.with_suffix(".corrupted.json")
            try:
                self.storage_path.rename(backup_path)
            except Exception:
                pass
            self.entries = []
            self.best_standard_entry_id = None

    def _save(self) -> None:
        payload = {
            "entries": [asdict(entry) for entry in self.entries],
            "best_standard_entry_id": self.best_standard_entry_id,
        }
        self.storage_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------
    def _find_entry(self, entry_id: str) -> Optional[DiaryEntry]:
        for entry in self.entries:
            if entry.entry_id == entry_id:
                return entry
        return None

    def _current_best_score(self) -> Optional[float]:
        if self.best_standard_entry_id:
            best_entry = self._find_entry(self.best_standard_entry_id)
            if best_entry and best_entry.proposed_standard_score is not None:
                return float(best_entry.proposed_standard_score)
        return None

    def _recalculate_best_standard(self) -> None:
        best_score: Optional[float] = None
        best_entry_id: Optional[str] = None

        for entry in self.entries:
            entry.is_current_best_standard = False
            score = entry.proposed_standard_score
            if score is None:
                continue
            if best_score is None or score > best_score:
                best_score = float(score)
                best_entry_id = entry.entry_id

        if best_entry_id:
            best_entry = self._find_entry(best_entry_id)
            if best_entry:
                best_entry.is_current_best_standard = True
        self.best_standard_entry_id = best_entry_id

    def get_best_standard(self) -> Optional[Dict[str, Any]]:
        best_entry = self._find_entry(self.best_standard_entry_id) if self.best_standard_entry_id else None
        return asdict(best_entry) if best_entry else None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def add_entry(
        self,
        component: str,
        summary: str,
        quality_metrics: Dict[str, float],
        validation_outcome: str,
        research_sources: Optional[List[str]] = None,
        lessons_learned: Optional[List[str]] = None,
        global_actions: Optional[List[str]] = None,
        proposed_standard: str = "",
        proposed_standard_score: Optional[float] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> DiaryEntry:
        """Add a diary entry and persist it.

        When a proposed standard score outranks the current benchmark, this
        method updates the best-standard pointer and flags the replacement.
        """

        timestamp = datetime.now(timezone.utc)
        entry_id = f"{timestamp.strftime('%Y%m%d%H%M%S')}-{len(self.entries) + 1:04d}"

        entry = DiaryEntry(
            entry_id=entry_id,
            timestamp_utc=timestamp.isoformat(),
            component=component,
            summary=summary,
            quality_metrics=dict(quality_metrics or {}),
            validation_outcome=validation_outcome,
            research_sources=list(research_sources or []),
            lessons_learned=list(lessons_learned or []),
            global_actions=list(global_actions or []),
            proposed_standard=proposed_standard,
            proposed_standard_score=float(proposed_standard_score) if proposed_standard_score is not None else None,
            tags=list(tags or []),
            metadata=dict(metadata or {}),
        )

        current_best_score = self._current_best_score()
        new_score = entry.proposed_standard_score
        if new_score is not None and (current_best_score is None or new_score > current_best_score):
            if self.best_standard_entry_id:
                previous_best = self._find_entry(self.best_standard_entry_id)
                if previous_best:
                    previous_best.is_current_best_standard = False
                    previous_best.superseded_by = entry.entry_id
                    entry.supersedes = previous_best.entry_id
            entry.is_current_best_standard = True
            self.best_standard_entry_id = entry.entry_id

        self.entries.append(entry)

        if self.max_entries and len(self.entries) > self.max_entries:
            self.entries = self.entries[-self.max_entries :]
            self._recalculate_best_standard()

        self._save()
        return entry

    def generate_summary(self, limit: int = 10) -> Dict[str, Any]:
        """Return a digest useful for dashboards or MCP responses."""

        sliced = self.entries[-limit:]
        return {
            "total_entries": len(self.entries),
            "best_standard": self.get_best_standard(),
            "recent_entries": [asdict(entry) for entry in sliced],
        }
