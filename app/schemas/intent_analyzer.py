from typing import List, Literal, Optional

from pydantic import BaseModel, Field, constr


class ExtractedInfo(BaseModel):
    address: Optional[str] = Field(None, description="Full address if present")
    zip_code: Optional[str] = Field(
        None, description="5-digit US ZIP code", max_length=5, min_length=5
    )
    year: Optional[int] = Field(None, description="Year if present (e.g., 2024)")
    month: Optional[int] = Field(None, ge=1, le=12, description="Month number (1-12)")
    crime_type: Optional[Literal["violent", "property", "other"]] = Field(
        None, description="If mentioned"
    )
    error: Optional[str] = Field(None, description="Any error that occurred")


class IntentAnalysis(BaseModel):
    needs_tools: bool
    intent_type: Literal["general", "crime", "flood", "location", "multi"]
    required_tools: List[str]
    requires_geocoding: bool
    extracted_info: ExtractedInfo
    reasoning: Optional[str]
