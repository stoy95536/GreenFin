"""
Demo Authentication & Session API.

This is a simplified session system for Demo purposes:
- No password, no JWT — just a session concept via user_id + role
- Admin sees all farmers
- Farmer sees only their own data
- Bank sees only authorized cases

For a real deployment this would be replaced with proper authentication (OAuth2, etc.)
"""

from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.app.models import User, UserRole, FarmerProfile, Farm, Crop
from backend.app.models.base import generate_id
from backend.app.repositories import (
    get_user_repo,
    get_farmer_repo,
    get_farm_repo,
    get_crop_repo,
)

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    user_id: str


class RegisterFarmerRequest(BaseModel):
    """Registration form for a new farmer."""
    username: str
    display_name: str
    real_name: str
    phone: Optional[str] = None
    address: Optional[str] = None
    farm_name: str
    farm_location: Optional[str] = None
    farm_area_hectares: Optional[float] = None
    crop_name: Optional[str] = None
    crop_variety: Optional[str] = None


@router.post("/login")
def api_login(request: LoginRequest):
    """
    Demo login — just verifies the user_id exists and returns their profile.

    No password check (Demo only).
    """
    user_repo = get_user_repo()
    user = user_repo.get_by_id(request.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="帳號不存在")

    # Get associated farmer profile if applicable
    farmer_profile = None
    if user.role == UserRole.FARMER:
        farmer_repo = get_farmer_repo()
        profiles = farmer_repo.find_by(user_id=user.id)
        if profiles:
            farmer_profile = profiles[0].model_dump()

    return {
        "user": user.model_dump(),
        "farmer_profile": farmer_profile,
        "message": f"歡迎，{user.display_name}",
    }


@router.get("/users")
def api_list_users():
    """List all users (for Demo login selection)."""
    user_repo = get_user_repo()
    users = user_repo.get_all()
    return {
        "users": [
            {
                "id": u.id,
                "username": u.username,
                "display_name": u.display_name,
                "role": u.role.value,
            }
            for u in users
        ],
    }


@router.post("/register")
def api_register_farmer(request: RegisterFarmerRequest):
    """
    Register a new farmer — creates User, FarmerProfile, Farm, and optionally Crop.

    Demo workflow: fill the form, press submit, get a profile ready to use.
    """
    user_repo = get_user_repo()
    farmer_repo = get_farmer_repo()
    farm_repo = get_farm_repo()
    crop_repo = get_crop_repo()

    # Check username uniqueness
    existing = user_repo.find_by(username=request.username)
    if existing:
        raise HTTPException(status_code=400, detail=f"帳號 '{request.username}' 已存在")

    # Create user
    user_id = f"user-{generate_id()[:8]}"
    user = User(
        id=user_id,
        username=request.username,
        display_name=request.display_name,
        role=UserRole.FARMER,
    )
    user_repo.create(user)

    # Create farm
    farm_id = f"farm-{generate_id()[:8]}"
    farm = Farm(
        id=farm_id,
        farmer_id="",  # Will be set after farmer profile created
        name=request.farm_name,
        location=request.farm_location,
        area_hectares=request.farm_area_hectares,
    )

    # Create farmer profile
    farmer_id = f"farmer-{generate_id()[:8]}"
    farmer = FarmerProfile(
        id=farmer_id,
        user_id=user_id,
        real_name=request.real_name,
        phone=request.phone,
        address=request.address,
        farm_ids=[farm_id],
    )
    farmer_repo.create(farmer)

    # Update farm with farmer_id
    farm.farmer_id = farmer_id
    farm_repo.create(farm)

    # Create crop if provided
    if request.crop_name:
        crop = Crop(
            id=f"crop-{generate_id()[:8]}",
            farm_id=farm_id,
            name=request.crop_name,
            variety=request.crop_variety,
        )
        crop_repo.create(crop)
        farm.crop_ids = [crop.id]
        farm_repo.update(farm)

    return {
        "message": "註冊成功！",
        "user": user.model_dump(),
        "farmer": farmer.model_dump(),
        "farm": farm.model_dump(),
    }


@router.get("/admin/farmers")
def api_admin_list_farmers():
    """
    Admin endpoint: list all farmers with summary info.

    In a real system this would check admin role. For Demo, accessible via the admin user.
    """
    farmer_repo = get_farmer_repo()
    farm_repo = get_farm_repo()

    farmers = farmer_repo.get_all()
    result = []
    for f in farmers:
        farms = farm_repo.find_by(farmer_id=f.id)
        result.append({
            "id": f.id,
            "user_id": f.user_id,
            "real_name": f.real_name,
            "phone": f.phone,
            "address": f.address,
            "farm_count": len(farms),
            "farms": [{"name": farm.name, "location": farm.location} for farm in farms],
        })

    return {
        "count": len(result),
        "farmers": result,
    }
