from app.schemas.flood_zone_tool import FloodZoneCoordinates
from app.services.flood_zone_service import FloodZoneService
from langchain.tools import StructuredTool

flood_zone_service = FloodZoneService()

flood_zone_service_flood_zone_details = StructuredTool.from_function(
    func=flood_zone_service.get_flood_zone_details,
    name="flood_zone_details",
    description="Get FEMA's Flood Zone code, a description of the code, and the risk level for given coordinates",
    args_schema=FloodZoneCoordinates,
)
