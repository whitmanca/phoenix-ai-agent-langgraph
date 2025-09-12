from pydantic import BaseModel, Field


class FloodZoneCoordinates(BaseModel):
    lat: float = Field(..., description="Latitude")
    lon: float = Field(..., description="Longitude")
