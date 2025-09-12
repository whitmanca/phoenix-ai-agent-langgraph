"""
This wrapper was designed to interact with the Phoenix Open Data API
which contains regularly updated crime data for the city of Phoenix.
The original intention was to pull the latest data on demand.
However, due to the lack of coordinate data within the datasets and the
resources required to geocode datasets of this magnitude, I have since opted
to download the CSV and geocode only records occurring on Jan 2025 - present
for demo purposes.
"""

import io
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import httpx
import pandas as pd

from app.core.config import settings

logger = logging.getLogger(__name__)


class PhoenixOpenDataClient:
    """Client for interacting with Phoenix Open Data CKAN API and CSV fallback"""

    def __init__(self):
        self.client = httpx.AsyncClient(
            timeout=settings.API_TIMEOUT,
            headers={"User-Agent": "Phoenix-AI-Assistant/1.0"},
        )
        self._schema_cache = None

    async def fetch_crime_data(
        self,
        limit: int = 10000,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        crime_types: Optional[List[str]] = None,
        use_api: bool = True,
    ) -> pd.DataFrame:
        """
        Fetch crime data using API first, fallback to CSV if needed

        Args:
            limit: Maximum number of records to fetch
            start_date: Filter for crimes after this date
            end_date: Filter for crimes before this date
            crime_types: List of crime types to filter for
            use_api: Whether to try API first (fallback to CSV if False)

        Returns:
            DataFrame with standardized crime data
        """
        if use_api:
            try:
                return await self._fetch_via_api(
                    limit, start_date, end_date, crime_types
                )
            except Exception as e:
                logger.warning(f"API fetch failed, falling back to CSV: {str(e)}")

        # Fallback to CSV
        return await self._fetch_via_csv(limit, start_date, end_date, crime_types)

    async def _fetch_via_api(
        self,
        limit: int,
        start_date: Optional[datetime],
        end_date: Optional[datetime],
        crime_types: Optional[List[str]],
    ) -> pd.DataFrame:
        """Fetch data using CKAN DataStore API"""

        # Build the query
        query_params = {
            "resource_id": settings.PHOENIX_CRIME_RESOURCE_ID,
            "limit": limit,
        }

        # Build filters for date range and crime types
        filters = {}

        # Add date filtering if provided
        if start_date or end_date:
            # First, get the schema to understand the date field format
            date_field = await self._get_date_field_name()
            if date_field:
                date_filter = {}
                if start_date:
                    date_filter[">="] = start_date.strftime("%Y-%m-%d")
                if end_date:
                    date_filter["<="] = end_date.strftime("%Y-%m-%d")
                if date_filter:
                    filters[date_field] = date_filter

        # Add crime type filtering
        if crime_types:
            crime_field = await self._get_crime_category_field_name()
            if crime_field:
                filters[crime_field] = crime_types

        if filters:
            query_params["filters"] = filters

        # Make the API request
        logger.info(f"Fetching crime data via API: {limit} records")

        response = await self.client.post(settings.PHOENIX_API_BASE, json=query_params)
        response.raise_for_status()

        data = response.json()

        if not data.get("success", False):
            raise Exception(f"API returned error: {data.get('error', 'Unknown error')}")

        # Convert to DataFrame
        records = data["result"]["records"]
        if not records:
            return pd.DataFrame()

        df = pd.DataFrame(records)
        logger.info(f"Successfully fetched {len(df)} records via API")

        return self._standardize_crime_data(df)

    async def _fetch_via_csv(
        self,
        limit: int,
        start_date: Optional[datetime],
        end_date: Optional[datetime],
        crime_types: Optional[List[str]],
    ) -> pd.DataFrame:
        """Fallback method using direct CSV download"""

        try:
            csv_url = f"{self.base_url}/dataset/0ce3411a-2fc6-4302-a33f-167f68608a20/resource/0ce3411a-2fc6-4302-a33f-167f68608a20/download/crimestat.csv"

            logger.info("Downloading Phoenix crime data CSV...")
            response = await self.client.get(csv_url)
            response.raise_for_status()

            # Parse CSV
            df = pd.read_csv(io.StringIO(response.text))
            logger.info(f"Successfully downloaded {len(df)} records via CSV")

            # Standardize the data
            df = self._standardize_crime_data(df)

            # Apply filters
            df = self._apply_filters(df, limit, start_date, end_date, crime_types)

            return df

        except Exception as e:
            logger.error(f"Error fetching CSV data: {str(e)}")
            raise

    async def _get_crime_category_field_name(self) -> Optional[str]:
        """Get the actual name of the crime category field"""
        schema = await self._get_resource_schema()

        # Look for crime category field patterns
        crime_patterns = ["crime", "category", "ucr"]
        for field in schema.get("fields", []):
            field_name = field.get("id", "").lower()
            if any(pattern in field_name for pattern in crime_patterns):
                return field.get("id")

        return "UCR CRIME CATEGORY"  # Default fallback

    def _apply_filters(
        self,
        df: pd.DataFrame,
        limit: int,
        start_date: Optional[datetime],
        end_date: Optional[datetime],
        crime_types: Optional[List[str]],
    ) -> pd.DataFrame:
        """Apply filters to DataFrame (used for CSV data)"""

        # Date filtering
        if (start_date or end_date) and "OCCURRED_ON" in df.columns:
            if start_date:
                df = df[df["OCCURRED_ON"] >= start_date]
            if end_date:
                df = df[df["OCCURRED_ON"] <= end_date]

        # Crime type filtering
        if crime_types and "UCR CRIME CATEGORY" in df.columns:
            df = df[df["UCR CRIME CATEGORY"].isin(crime_types)]

        # Apply limit
        if len(df) > limit:
            df = df.head(limit)

        return df

    def _standardize_crime_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Standardize column names and data types

        Args:
            df: Raw DataFrame from API or CSV

        Returns:
            Standardized DataFrame
        """
        # Standardize column names
        df.columns = df.columns.str.upper().str.strip()

        # Convert date columns
        if "OCCURRED ON" in df.columns:
            df["OCCURRED_ON"] = pd.to_datetime(df["OCCURRED ON"], errors="coerce")
            df["OCCURRED_DATE"] = df["OCCURRED_ON"].dt.date
            df["OCCURRED_HOUR"] = df["OCCURRED_ON"].dt.hour
            df["DAY_OF_WEEK"] = df["OCCURRED_ON"].dt.day_name()

        # Clean and standardize coordinate columns
        coord_columns = ["X", "Y", "LATITUDE", "LONGITUDE"]
        for col in coord_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        # Standardize crime category
        if "UCR CRIME CATEGORY" in df.columns:
            df["UCR CRIME CATEGORY"] = df["UCR CRIME CATEGORY"].str.upper().str.strip()

        # Remove rows with null coordinates
        coord_cols = self._get_coordinate_columns(df)
        if coord_cols:
            df = df.dropna(subset=coord_cols)
            df = self._filter_valid_coordinates(df, coord_cols)

        return df

    def _get_coordinate_columns(self, df: pd.DataFrame) -> List[str]:
        """Get available coordinate columns"""
        if "LATITUDE" in df.columns and "LONGITUDE" in df.columns:
            return ["LATITUDE", "LONGITUDE"]
        elif "X" in df.columns and "Y" in df.columns:
            return ["X", "Y"]
        return []

    def _filter_valid_coordinates(
        self, df: pd.DataFrame, coord_cols: List[str]
    ) -> pd.DataFrame:
        """Filter out invalid coordinates"""
        if coord_cols == ["LATITUDE", "LONGITUDE"]:
            # Phoenix area bounds approximately
            df = df[
                (df["LATITUDE"].between(33.0, 34.0))
                & (df["LONGITUDE"].between(-113.0, -111.0))
            ]
        elif coord_cols == ["X", "Y"]:
            # Filter out obviously bad coordinates (0,0)
            df = df[(df["X"] != 0) & (df["Y"] != 0)]

        return df

    async def search_with_sql(self, sql_query: str) -> pd.DataFrame:
        """
        Execute a SQL query against the datastore

        Args:
            sql_query: SQL query string

        Returns:
            DataFrame with query results
        """
        try:
            url = f"{self.base_url}/api/3/action/datastore_search_sql"
            params = {"sql": sql_query}

            response = await self.client.post(url, json=params)
            response.raise_for_status()

            data = response.json()
            if not data.get("success", False):
                raise Exception(
                    f"SQL query failed: {data.get('error', 'Unknown error')}"
                )

            records = data["result"]["records"]
            if not records:
                return pd.DataFrame()

            df = pd.DataFrame(records)
            return self._standardize_crime_data(df)

        except Exception as e:
            logger.error(f"SQL query failed: {str(e)}")
            raise

    async def get_crime_stats_summary(self, days_back: int = 30) -> Dict[str, Any]:
        """
        Get a quick summary of crime statistics using SQL

        Args:
            days_back: Number of days to look back

        Returns:
            Dictionary with summary statistics
        """
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days_back)

            sql = f"""
            SELECT 
                "UCR CRIME CATEGORY" as crime_type,
                COUNT(*) as incident_count,
                AVG(EXTRACT(hour FROM "OCCURRED ON"::timestamp)) as avg_hour
            FROM "{self.resource_id}"
            WHERE "OCCURRED ON"::date >= '{start_date.strftime("%Y-%m-%d")}'
            AND "OCCURRED ON"::date <= '{end_date.strftime("%Y-%m-%d")}'
            GROUP BY "UCR CRIME CATEGORY"
            ORDER BY incident_count DESC
            LIMIT 20
            """

            df = await self.search_with_sql(sql)

            if df.empty:
                return {}

            return {
                "total_incidents": df["incident_count"].sum(),
                "crime_breakdown": df.set_index("crime_type")[
                    "incident_count"
                ].to_dict(),
                "period_days": days_back,
                "daily_average": df["incident_count"].sum() / days_back,
            }

        except Exception as e:
            logger.warning(
                f"Could not fetch SQL summary, falling back to basic fetch: {str(e)}"
            )
            # Fallback to regular fetch
            df = await self.fetch_crime_data(
                limit=1000, start_date=start_date, end_date=end_date
            )

            if df.empty:
                return {}

            crime_counts = (
                df["UCR CRIME CATEGORY"].value_counts()
                if "UCR CRIME CATEGORY" in df.columns
                else {}
            )

            return {
                "total_incidents": len(df),
                "crime_breakdown": crime_counts.to_dict(),
                "period_days": days_back,
                "daily_average": len(df) / days_back,
            }

    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()
