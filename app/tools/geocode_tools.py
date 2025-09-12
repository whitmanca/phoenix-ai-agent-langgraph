from langchain.tools import StructuredTool

from app.schemas.geocode_tool import GeocodeAddress, GeocodeCoordinates
from app.services.geocode import GeocodeService

geocode_service = GeocodeService()

geocode_address = StructuredTool.from_function(
    func=geocode_service.geocode,
    name="geocode_address",
    description="Get the coordinates for a FULL address (must include city and state). Example: '223 N 7th Ave, Phoenix, AZ'",
    args_schema=GeocodeAddress,
)

reverse_geocode = StructuredTool.from_function(
    func=geocode_service.reverse_geocode,
    name="reverse_geocode",
    description="Convert coordinates to an address",
    args_schema=GeocodeCoordinates,
)

geocode_street_name = StructuredTool.from_function(
    func=geocode_service.get_geocode_with_street,
    name="geocode_street_name",
    description="Get the coordinates for a PARTIAL address that only contains the street name/number WITHOUT city/state. Example: '223 N 7th Ave'",
    args_schema=GeocodeAddress,
)
