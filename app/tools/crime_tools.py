from langchain.tools import StructuredTool

from app.schemas.crime_tool import CrimeZip
from app.services.crime_service import CrimeService

crime_service = CrimeService()

crime_service_total_counts_by_zip = StructuredTool.from_function(
    func=crime_service.extract_crime_counts_by_zip,
    name="crime_service_total_counts_by_zip",
    description="Get the total crime counts for a specific single ZIP code",
    args_schema=CrimeZip,
)

crime_service_trends_by_year = StructuredTool.from_function(
    func=crime_service.extract_crime_trends_by_year,
    name="crime_service_trends_by_year",
    description="Get crime trends and statistics broken down by year for a single ZIP code",
    args_schema=CrimeZip,
)

crime_service_seasonal_trends = StructuredTool.from_function(
    func=crime_service.extract_seasonal_trends,
    name="crime_service_seasonal_trends",
    description="Get crime trends and statistics broken down by month for a single ZIP code",
    args_schema=CrimeZip,
)

crime_service_recent_activity = StructuredTool.from_function(
    func=crime_service.extract_recent_trends_and_safety_indicators,
    name="crime_service_recent_activity",
    description="Get recent crime trends within the last two years for a ZIP code "
    "and severity analysis based on crime type: violent vs property",
    args_schema=CrimeZip,
)

crime_heatmap_tool = StructuredTool.from_function(
    func=crime_service.get_recent_crimes_with_geos,
    name="crime_heatmap",
    description="Get recent crime incidents as points for density visualization",
    args_schema=CrimeZip,
)
