import os
from pathlib import Path
from typing import List


class Settings:
    """Application settings"""

    PROJECT_ROOT = Path(__file__).parent.parent.parent

    # API Configuration
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Phoenix AI Assistant"
    API_TIMEOUT: int = 120

    # Phoenix Open Data Configuration
    PHOENIX_API_BASE: str = "https://www.phoenixopendata.com/api/3/action"
    PHOENIX_CRIME_RESOURCE_ID: str = "0ce3411a-2fc6-4302-a33f-167f68608a20"
    CRIME_DATA_CSV_URL: str = (
        "https://www.phoenixopendata.com/dataset/0ce3411a-2fc6-4302-a33f-167f68608a20/resource/0ce3411a-2fc6-4302-a33f-167f68608a20/download/crimestat.csv"
    )
    CRIME_DATA_CSV: str = str(
        PROJECT_ROOT / "app/data/crime-data_crime-data_crimestat.csv"
    )
    CRIME_2025_CSV: str = str(PROJECT_ROOT / "app/data/crime_geodata_2025.csv")
    ZIP_CODES_GEOJSON: str = str(PROJECT_ROOT / "app/data/zip_codes.geojson")

    # FEMA API Configuration
    FEMA_API_BASE: str = (
        "https://hazards.fema.gov/arcgis/rest/services/public/NFHL/MapServer/28/query"
    )
    FEMA_ZONE_KEY: str = "FLD_ZONE"
    FEMA_SUB_TYPE_KEY: str = "ZONE_SUBTY"

    # LLM Configuration (optional - for enhanced analysis)
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    GROQ_TEMPERATURE: int = 0
    MAX_REQUESTS_PER_MINUTE: int = 60

    # Logging
    LOG_LEVEL: str = "INFO"

    # CORS
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000"]  # React dev server

    class Config:
        env_file = ".env"


settings = Settings()
