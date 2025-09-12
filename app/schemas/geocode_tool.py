from pydantic import BaseModel, Field


class GeocodeAddress(BaseModel):
    address: str = Field(
        ..., description="The address string to convert to coordinates"
    )


class GeocodeCoordinates(BaseModel):
    lat: float = Field(..., description="Latitude")
    lon: float = Field(..., description="Longitude")
