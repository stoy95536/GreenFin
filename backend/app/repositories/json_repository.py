"""
Generic JSON File Repository.

Provides CRUD operations for Pydantic models stored as JSON files.
One JSON file per entity type, each containing a list of records.

Per ADR-0006: Demo uses JSON files instead of SQL database.
Repository interface is designed so a SQL implementation can replace it later.
"""

import json
from pathlib import Path
from typing import Generic, Optional, TypeVar

from pydantic import BaseModel

from backend.app.models.base import EntityBase, now_taipei

T = TypeVar("T", bound=EntityBase)

# Default data directory
DATA_DIR = Path(__file__).resolve().parents[2] / "data"


class JsonRepository(Generic[T]):
    """
    Generic repository for JSON file-based CRUD operations.

    Each entity type gets its own JSON file (e.g. data/users.json).
    The file contains a JSON array of serialized entity objects.
    """

    def __init__(self, model_class: type[T], filename: str, data_dir: Path = DATA_DIR):
        """
        Initialize repository.

        Args:
            model_class: The Pydantic model class for deserialization.
            filename: JSON filename (e.g. "users.json").
            data_dir: Directory where JSON files are stored.
        """
        self.model_class = model_class
        self.data_dir = data_dir
        self.file_path = data_dir / filename

        # Ensure data directory exists
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Create empty file if it doesn't exist
        if not self.file_path.exists():
            self._write_all([])

    def _read_all_raw(self) -> list[dict]:
        """Read all raw records from JSON file."""
        if not self.file_path.exists():
            return []
        content = self.file_path.read_text(encoding="utf-8")
        if not content.strip():
            return []
        return json.loads(content)

    def _write_all(self, records: list[dict]) -> None:
        """Write all records to JSON file."""
        self.file_path.write_text(
            json.dumps(records, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def get_all(self) -> list[T]:
        """Get all entities."""
        raw = self._read_all_raw()
        return [self.model_class.model_validate(r) for r in raw]

    def get_by_id(self, entity_id: str) -> Optional[T]:
        """Get a single entity by ID. Returns None if not found."""
        raw = self._read_all_raw()
        for record in raw:
            if record.get("id") == entity_id:
                return self.model_class.model_validate(record)
        return None

    def find_by(self, **kwargs) -> list[T]:
        """
        Find entities matching all provided field=value pairs.

        Example: repo.find_by(farmer_id="abc", domain="IDENTITY")
        """
        raw = self._read_all_raw()
        results = []
        for record in raw:
            match = all(record.get(k) == v for k, v in kwargs.items())
            if match:
                results.append(self.model_class.model_validate(record))
        return results

    def find_one_by(self, **kwargs) -> Optional[T]:
        """Find first entity matching criteria. Returns None if not found."""
        results = self.find_by(**kwargs)
        return results[0] if results else None

    def create(self, entity: T) -> T:
        """
        Add a new entity. Returns the created entity.

        Raises ValueError if an entity with the same ID already exists.
        """
        raw = self._read_all_raw()

        # Check for duplicate ID
        for record in raw:
            if record.get("id") == entity.id:
                raise ValueError(f"Entity with id '{entity.id}' already exists")

        raw.append(entity.model_dump())
        self._write_all(raw)
        return entity

    def update(self, entity: T) -> T:
        """
        Update an existing entity. Matches by ID.

        Raises ValueError if entity not found.
        """
        raw = self._read_all_raw()
        found = False

        for i, record in enumerate(raw):
            if record.get("id") == entity.id:
                entity.touch()
                raw[i] = entity.model_dump()
                found = True
                break

        if not found:
            raise ValueError(f"Entity with id '{entity.id}' not found")

        self._write_all(raw)
        return entity

    def delete(self, entity_id: str) -> bool:
        """
        Delete an entity by ID. Returns True if deleted, False if not found.
        """
        raw = self._read_all_raw()
        original_len = len(raw)
        raw = [r for r in raw if r.get("id") != entity_id]

        if len(raw) == original_len:
            return False

        self._write_all(raw)
        return True

    def count(self) -> int:
        """Return total number of entities."""
        return len(self._read_all_raw())

    def exists(self, entity_id: str) -> bool:
        """Check if an entity with given ID exists."""
        raw = self._read_all_raw()
        return any(r.get("id") == entity_id for r in raw)

    def clear(self) -> None:
        """Remove all entities. Use with caution (mainly for testing)."""
        self._write_all([])
