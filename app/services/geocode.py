from geopy.geocoders import Nominatim


class GeocodeService:
    """Service layer for geocoding business logic"""

    def __init__(self):
        self.geocoder = Nominatim(user_agent="phoenix-ai-assistant", timeout=(10, 10))

    def geocode(self, address: str):
        """Geocode an address"""
        location = self.geocoder.geocode(address, addressdetails=True)
        if location:
            return {
                "lat": location.latitude,
                "lon": location.longitude,
                "zip_code": location.raw["address"].get("postcode"),
                "address": location.address,
                "geometry": location.point,
            }
        return None

    def reverse_geocode(self, lat: float, lon: float):
        """Reverse geocode coordinates"""
        location = self.geocoder.reverse(
            (lat, lon), exactly_one=True, addressdetails=True
        )
        if location:
            return {
                "lat": location.latitude,
                "lon": location.longitude,
                "zip_code": location.raw["address"].get("postcode"),
                "address": location.address,
                "geometry": location.point,
            }
        return None

    def get_geocode_with_street(self, address: str):
        """Get the geocode of a street name by adding city and state"""
        new_address = f"{address}, Phoenix, Arizona"
        return self.geocode(new_address)
