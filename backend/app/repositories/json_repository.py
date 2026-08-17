"""
Generic JSON File Repository.

Provides CRUD operations for Pydantic models stored as JSON files.
One JSON file per entity type, each containing a list of records.

Per ADR-0006: Demo uses JSON files instead of SQL database.
Repository interface is designed so a SQL implementation can replace it later.

Design notes:
- The data directory is resolved lazily via core.storage.get_data_dir(). It is
  deliberately NOT a default argument: binding a Path as a default freezes it at
  import time and makes runtime/test overrides silently ineffective.
- Mutations go through storage.mutate_json_atomic(), which holds the write lock for
  the whole read-modify-write cycle and replaces the file atomically.
"""

from pathlib import Path
from typing import Generic, Optional, TypeVar

from backend.app.core.storage import (
    get_data_dir,
    mutate_json_atomic,
    read_json,
    write_json_atomic,
)
from backend.app.models.base import EntityBase

T = TypeVar("T", bound=EntityBase)


class JsonRepository(Generic[T]):
    """
    Generic repository for JSON file-based CRUD operations.

    Each entity type gets its own JSON file (e.g. data/users.json).
    The file contains a JSON array of serialized entity objects.
    """

    def __init__(self, model_class: type[T], filename: str, data_dir: Optional[Path] = None):
        """
        Initialize repository.

        Args:
            model_class: The Pydantic model class for deserialization.
            filename: JSON filename (e.g. "users.json").
            data_dir: Optional explicit directory. When None (the normal case) the
                      active directory is resolved lazily on every access, so test
                      and deployment overrides always apply.
        """
        self.model_class = model_class
        self.filename = filename
        self._explicit_data_dir = Path(data_dir) if data_dir is not None else None

    @property
    def data_dir(self) -> Path:
        """Active data directory, resolved at access time."""
        return self._explicit_data_dir if self._explicit_data_dir is not None else get_data_dir()

    @property
    def file_path(self) -> Path:
        """Full path to this repository's JSON file, resolved at access time."""
        return self.data_dir / self.filename

    # ─── Reads ────────────────────────────────────────────────────────────────

    def _read_all_raw(self) -> list[dict]:
        """Read all raw records from the JSON file."""
        return read_json(self.file_path)

    def get_all(self) -> list[T]:
        """Get all entities."""
        return [self.model_class.model_validate(r) for r in self._read_all_raw()]

    def get_by_id(self, entity_id: str) -> Optional[T]:
        """Get a single entity by ID. Returns None if not found."""
        for record in self._read_all_raw():
            if record.get("id") == entity_id:
                return self.model_class.model_validate(record)
        return None

    def find_by(self, **kwargs) -> list[T]:
        """
        Find entities matching all provided field=value pairs.

        Example: repo.find_by(farmer_id="abc", domain="IDENTITY")
        """
        results = []
        for record in self._read_all_raw():
            if all(record.get(k) == v for k, v in kwargs.items()):
                results.append(self.model_class.model_validate(record))
        return results

    def find_one_by(self, **kwargs) -> Optional[T]:
        """Find first entity matching criteria. Returns None if not found."""
        results = self.find_by(**kwargs)
        return results[0] if results else None

    def count(self) -> int:
        """Return total number of entities."""
        return len(self._read_all_raw())

    def exists(self, entity_id: str) -> bool:
        """Check if an entity with given ID exists."""
        return any(r.get("id") == entity_id for r in self._read_all_raw())

    # ─── Mutations (atomic, lock held across read-modify-write) ───────────────

    def create(self, entity: T) -> T:
        """
        Add a new entity. Returns the created entity.

        Raises ValueError if an entity with the same ID already exists.
        """
        def mutator(records: list[dict]):
            for record in records:
                if record.get("id") == entity.id:
                    raise ValueError(f"Entity with id '{entity.id}' already exists")
            return records + [entity.model_dump(mode="json")], entity

        return mutate_json_atomic(self.file_path, mutator)

    def update(self, entity: T) -> T:
        """
        Update an existing entity. Matches by ID.

        Raises ValueError if entity not found.
        """
        def mutator(records: list[dict]):
            for i, record in enumerate(records):
                if record.get("id") == entity.id:
                    entity.touch()
                    updated = list(records)
                    updated[i] = entity.model_dump(mode="json")
                    return updated, entity
            raise ValueError(f"Entity with id '{entity.id}' not found")

        return mutate_json_atomic(self.file_path, mutator)

    def delete(self, entity_id: str) -> bool:
        """
        Delete an entity by ID. Returns True if deleted, False if not found.
        """
        def mutator(records: list[dict]):
            remaining = [r for r in records if r.get("id") != entity_id]
            return remaining, len(remaining) != len(records)

        return mutate_json_atomic(self.file_path, mutator)

    def clear(self) -> None:
        """Remove all entities. Use with caution (mainly for testing/seeding)."""
        write_json_atomic(self.file_path, [])
