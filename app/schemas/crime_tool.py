from pydantic import BaseModel, Field


class CrimeZip(BaseModel):
    zip_code: str = Field(..., description="The zip code to get crime data for")
