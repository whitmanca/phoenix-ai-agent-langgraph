import json
from typing import Any, Dict, Optional

import requests
from app.core.config import settings
from app.data.flood_zone_definitions import FLOOD_ZONE_DEFS


class FloodZoneService:
    """Service layer for FEMA's flood zone-related business logic"""

    def __init__(self):
        self.api_base = settings.FEMA_API_BASE
        self.api_params = {
            "where": "1=1",
            "geometryType": "esriGeometryPoint",
            "spatialRel": "esriSpatialRelIntersects",
            "outFields": "*",
            "returnGeometry": "false",
            "f": "json",
        }
        self.zone_key = settings.FEMA_ZONE_KEY
        self.zone_sub_type_key = settings.FEMA_SUB_TYPE_KEY
        self.zone_descriptions = FLOOD_ZONE_DEFS
        self.timeout = settings.API_TIMEOUT
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "FloodZoneService/1.0"})

    def fetch_fema_flood_zone_data(self, lat: float, lon: float) -> Dict[str, Any]:
        """Query the FEMA API for a given lat and lon"""
        # Validate coordinates
        if not (-90 <= lat <= 90):
            raise ValueError(f"Invalid latitude: {lat}. Must be between -90 and 90")
        if not (-180 <= lon <= 180):
            raise ValueError(f"Invalid longitude: {lon}. Must be between -180 and 180")

        params = {**self.api_params}
        params["geometry"] = f"{lon},{lat}"

        try:
            response = self.session.get(
                self.api_base, params=params, timeout=self.timeout
            )
            response.raise_for_status()

            data = response.json()

            if "error" in data:
                error_msg = data["error"].get("message", "Unknown API error")
                raise requests.RequestException(f"FEMA API error: {error_msg}")

            return data

        except requests.exceptions.Timeout:
            raise requests.RequestException(
                f"Request timed out after {self.timeout} seconds"
            )
        except requests.exceptions.ConnectionError:
            raise requests.RequestException("Failed to connect to FEMA API")
        except requests.exceptions.HTTPError as e:
            raise requests.RequestException(
                f"HTTP error {e.response.status_code}: {e.response.reason}"
            )
        except json.JSONDecodeError:
            raise requests.RequestException("Invalid JSON response from FEMA API")

    def get_flood_zone_details(self, lat: float, lon: float) -> Dict[str, Any]:
        """Get detailed flood zone information for a coordinate"""

        result = {
            "coordinates": {"lat": lat, "lon": lon},
            "flood_zone": None,
            "description": None,
            "risk_level": None,
            "found": False,
            "error": None,
        }

        try:
            data = self.fetch_fema_flood_zone_data(lat, lon)

            if data.get("features"):
                attributes = data["features"][0]["attributes"]
                flood_zone = attributes.get(self.zone_key)
                details = self._get_description_and_risk_level(attributes)

                result.update(
                    {"flood_zone": flood_zone, "found": bool(flood_zone), **details}
                )

        except (requests.RequestException, ValueError) as e:
            result["error"] = str(e)

        return result

    def _get_description_and_risk_level(self, attributes: dict) -> Dict[str, str]:
        """Get the flood zone code's description and risk level"""

        zone = attributes.get(self.zone_key)
        zone_subty = attributes.get(self.zone_sub_type_key, "")

        # Determine if X zone is shaded or unshaded
        if zone == "X":
            if "0.2 PCT ANNUAL CHANCE" in zone_subty.upper():
                zone_classification = "X (Shaded)"
            else:
                zone_classification = "X (Unshaded)"
        else:
            zone_classification = zone

        # Fallback response
        no_results = {
            "description": "Could not determine description for flood zone",
            "risk_level": "Unknown",
        }

        return self.zone_descriptions.get(zone_classification, no_results)

    def close(self):
        """Close the requests session"""
        self.session.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
