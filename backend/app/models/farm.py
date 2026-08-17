"""
Farm and Crop models.
"""

from typing import Optional

from pydantic import Field

from backend.app.models.base import EntityBase


class Farm(EntityBase):
    """A farmer's farm/land plot."""

    farmer_id: str = Field(..., description="Reference to FarmerProfile.id")
    name: str = Field(..., description="Farm name (e.g. 綠田友善農場)")
    location: Optional[str] = Field(default=None, description="Location description")
    area_hectares: Optional[float] = Field(default=None, description="Area in hectares")
    crop_ids: list[str] = Field(default_factory=list, description="List of Crop IDs")


class Crop(EntityBase):
    """Crop grown on a farm."""

    farm_id: str = Field(..., description="Reference to Farm.id")
    name: str = Field(..., description="Crop name (e.g. 稻米)")
    variety: Optional[str] = Field(default=None, description="Variety/cultivar")
    planting_season: Optional[str] = Field(default=None, description="Planting season")
