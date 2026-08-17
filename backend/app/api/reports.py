"""
Report API Endpoints.

Bank Information Package generation.
"""

from fastapi import APIRouter, HTTPException

from backend.app.services.reports.package import ReportError, generate_bank_information_package

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/bank-package/{institution_id}/{farmer_id}")
def api_generate_bank_package(institution_id: str, farmer_id: str):
    """
    Generate the Bank Information Package for an authorized case.

    This is the primary deliverable: a structured, traceable, explainable
    data package summarizing the farmer's green profile.

    Requires valid authorization.
    """
    try:
        package = generate_bank_information_package(farmer_id, institution_id)
    except ReportError as e:
        raise HTTPException(status_code=403, detail=str(e))

    return package
