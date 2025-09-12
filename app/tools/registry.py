from app.tools.crime_tools import (
    crime_heatmap_tool,
    crime_service_recent_activity,
    crime_service_seasonal_trends,
    crime_service_total_counts_by_zip,
    crime_service_trends_by_year,
)
from app.tools.flood_zone_tools import flood_zone_service_flood_zone_details
from app.tools.geocode_tools import (
    geocode_address,
    geocode_street_name,
    reverse_geocode,
)

DATA_TOOLS = {
    t.name: t
    for t in [
        crime_service_total_counts_by_zip,
        crime_service_trends_by_year,
        crime_service_seasonal_trends,
        crime_service_recent_activity,
        geocode_address,
        geocode_street_name,
        reverse_geocode,
        flood_zone_service_flood_zone_details,
    ]
}
VISUALIZATION_TOOLS = {t.name: t for t in [crime_heatmap_tool]}


ALL_TOOLS = {**DATA_TOOLS, **VISUALIZATION_TOOLS}
