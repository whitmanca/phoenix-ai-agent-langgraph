from datetime import datetime

import numpy as np
import pandas as pd

from app.core.config import settings


class CrimeService:
    """Service layer for crime-related business logic"""

    def __init__(self):
        self.columns = {
            "incident_number": "INC NUMBER",
            "occurred_on": "OCCURRED ON",
            "occurred_to": "OCCURRED TO",
            "crime_category": "UCR CRIME CATEGORY",
            "address": "100 BLOCK ADDR",
            "zip_code": "ZIP",
            "premise_type": "PREMISE TYPE",
            "grid": "GRID",
        }
        self.crime_data = self._clean_crime_data(settings.CRIME_DATA_CSV)
        self.crime_2025 = self._clean_crime_data(settings.CRIME_2025_CSV)

    def get_crime_data(self):
        return self.crime_data

    def _clean_crime_data(self, f):
        df = pd.read_csv(f, dtype={"ZIP": str})

        # Remap columns
        if "geometry" in df.columns:
            self.columns["geometry"] = "geometry"
        df = df[self.columns.values()]
        df.columns = self.columns.keys()

        # Clean up datetime fields
        primary_col = "occurred_on"
        fallback_col = "occurred_to"

        # Convert both columns to datetime
        df[primary_col] = pd.to_datetime(df[primary_col], errors="coerce")
        df[fallback_col] = pd.to_datetime(df[fallback_col], errors="coerce")

        # Create a combined datetime column that uses fallback when primary is NaT
        df["datetime_combined"] = df[primary_col].fillna(df[fallback_col])

        # Extract components from the combined datetime
        df["YEAR"] = df["datetime_combined"].dt.year.fillna(-1).astype(int)
        df["MONTH"] = df["datetime_combined"].dt.month.fillna(-1).astype(int)
        df["DAY"] = df["datetime_combined"].dt.day.fillna(-1).astype(int)
        df["HOUR"] = df["datetime_combined"].dt.hour.fillna(-1).astype(int)
        df["MINUTE"] = df["datetime_combined"].dt.minute.fillna(-1).astype(int)
        df["SECOND"] = df["datetime_combined"].dt.second.fillna(-1).astype(int)

        # Handle NaN values in ZIP column
        df["zip_code"] = df["zip_code"].fillna("00000").astype(str)
        return df

    def _filter_by_zip(self, zip_code: str) -> pd.DataFrame:
        """Filter the crime data frame by zip code"""
        zip_data = self.crime_data[self.crime_data["zip_code"] == zip_code].copy()
        return zip_data

    def _initialize_response(self, df: pd.DataFrame, zip_code: str):
        """
        Initialize the stats dictionary
        """
        years_available = sorted(df["YEAR"].unique())

        # Initialize stats dictionary
        stats = {
            "zip_code": str(zip_code),
            "analysis_date": datetime.now().isoformat(),
            "data_period": {
                "earliest_year": int(years_available[0]) if years_available else None,
                "latest_year": int(years_available[-1]) if years_available else None,
                "total_years_of_data": len(years_available),
            },
        }

        return stats

    def _calculate_rate_of_change(self, zip_data: pd.DataFrame, years_back: int):
        """Helper method to calculate rate of change for any timeframe"""
        years_available = sorted(zip_data["YEAR"].unique())
        yearly_counts = zip_data.groupby("YEAR").size().to_dict()

        if len(years_available) < years_back + 1:
            return None

        latest_year = years_available[-1]
        target_year = latest_year - years_back

        if target_year not in yearly_counts:
            return None

        latest_count = yearly_counts[latest_year]
        target_count = yearly_counts[target_year]

        if target_count == 0:
            return None

        rate_of_change = ((latest_count - target_count) / target_count) * 100
        return round(rate_of_change, 2)

    def extract_crime_counts_by_zip(self, zip_code: str):
        """
        Extract counts of crime events broken down by crime category
        """
        # Filter the data
        zip_data = self._filter_by_zip(zip_code)
        if zip_data.empty:
            return None

        # Initialize the response stats object
        stats = self._initialize_response(zip_data, zip_code)

        # Total counts
        stats["total_incidents"] = len(zip_data)

        # Crime type breakdown
        crime_type_counts = zip_data["crime_category"].value_counts().to_dict()
        stats["crime_types"] = {
            "breakdown": crime_type_counts,
            "most_common": (
                zip_data["crime_category"].mode().iloc[0]
                if not zip_data.empty
                else None
            ),
            "total_unique_types": len(crime_type_counts),
        }

        return stats

    def extract_crime_trends_by_year(self, zip_code: str):
        """
        Extract yearly crime trends by zip code
        """
        # Filter the data
        zip_data = self._filter_by_zip(zip_code)
        if zip_data.empty:
            return None

        # Initialize the response stats object
        stats = self._initialize_response(zip_data, zip_code)

        # Get all years available in the dataset
        years_available = sorted(zip_data["YEAR"].unique())

        # Yearly statistics
        yearly_counts = zip_data.groupby("YEAR").size().to_dict()
        stats["yearly_statistics"] = {
            "counts_by_year": {
                int(year): int(count) for year, count in yearly_counts.items()
            },
            "average_incidents_per_year": float(np.mean(list(yearly_counts.values()))),
            "peak_year": (
                int(max(yearly_counts, key=yearly_counts.get))
                if yearly_counts
                else None
            ),
            "lowest_year": (
                int(min(yearly_counts, key=yearly_counts.get))
                if yearly_counts
                else None
            ),
        }

        stats["rate_of_change"] = {
            "one_year": self._calculate_rate_of_change(zip_data, 1),
            "three_year": self._calculate_rate_of_change(zip_data, 3),
            "five_year": self._calculate_rate_of_change(zip_data, 5),
        }

        return stats

    def extract_seasonal_trends(self, zip_code: str):
        """
        Extract seasonal crime trends broken down by month
        """
        # Filter the data
        zip_data = self._filter_by_zip(zip_code)
        if zip_data.empty:
            return None

        # Initialize the response stats object
        stats = self._initialize_response(zip_data, zip_code)

        # Monthly patterns
        monthly_counts = zip_data["MONTH"].value_counts().sort_index().to_dict()
        month_names = {
            1: "January",
            2: "February",
            3: "March",
            4: "April",
            5: "May",
            6: "June",
            7: "July",
            8: "August",
            9: "September",
            10: "October",
            11: "November",
            12: "December",
        }

        stats["seasonal_patterns"] = {
            "monthly_counts": {
                month_names[month]: count for month, count in monthly_counts.items()
            },
            "peak_month": (
                month_names[max(monthly_counts, key=monthly_counts.get)]
                if monthly_counts
                else None
            ),
            "lowest_month": (
                month_names[min(monthly_counts, key=monthly_counts.get)]
                if monthly_counts
                else None
            ),
            "average_per_month": (
                round(len(zip_data) / len(monthly_counts), 2) if monthly_counts else 0
            ),
        }

        return stats

    def extract_recent_trends_and_safety_indicators(self, zip_code: str):
        """
        Extract data about recent trends within the last two years
        and severity analysis based on crime type: violent vs property
        """
        # Filter the data
        zip_data = self._filter_by_zip(zip_code)
        if zip_data.empty:
            return None

        # Initialize the response stats object
        stats = self._initialize_response(zip_data, zip_code)

        # Get all years available in the dataset
        years_available = sorted(zip_data["YEAR"].unique())

        total_incidents = len(zip_data)
        yearly_counts = zip_data.groupby("YEAR").size().to_dict()

        # Recent trends (last 2 years if available)
        recent_years = [
            year for year in years_available if year >= max(years_available) - 1
        ]
        recent_data = zip_data[zip_data["YEAR"].isin(recent_years)]

        stats["recent_trends"] = {
            "last_two_years_total": len(recent_data),
            "recent_crime_types": recent_data["crime_category"]
            .value_counts()
            .head(5)
            .to_dict(),
            "recent_average_per_year": (
                round(len(recent_data) / len(recent_years), 2) if recent_years else 0
            ),
        }

        # Safety indicators
        latest_year_count = (
            yearly_counts.get(years_available[-1], 0) if years_available else 0
        )
        historical_average = (
            np.mean(list(yearly_counts.values())) if yearly_counts else 0
        )

        # Determine trend direction
        stats["rate_of_change"] = {
            "one_year": self._calculate_rate_of_change(zip_data, 1),
            "three_year": self._calculate_rate_of_change(zip_data, 3),
            "five_year": self._calculate_rate_of_change(zip_data, 5),
        }
        trend_direction = "stable"
        if stats["rate_of_change"]["one_year"]:
            if stats["rate_of_change"]["one_year"] > 10:
                trend_direction = "increasing"
            elif stats["rate_of_change"]["one_year"] < -10:
                trend_direction = "decreasing"

        stats["safety_indicators"] = {
            "current_vs_historical_average": {
                "latest_year_incidents": latest_year_count,
                "historical_average": round(historical_average, 2),
                "above_average": latest_year_count > historical_average,
            },
            "trend_direction": trend_direction,
            "incidents_per_day_recent": (
                round(latest_year_count / 365, 3) if latest_year_count > 0 else 0
            ),
        }

        # Crime severity analysis (if we can infer from crime types)
        violent_crimes = [
            "assault",
            "robbery",
            "homicide",
            "rape",
            "murder",
            "battery",
            "domestic violence",
        ]
        property_crimes = [
            "burglary",
            "theft",
            "larceny",
            "vandalism",
            "arson",
            "auto theft",
        ]

        zip_data_lower = zip_data.copy()
        zip_data_lower["crime_type_lower"] = zip_data_lower[
            "crime_category"
        ].str.lower()

        violent_count = sum(
            zip_data_lower["crime_type_lower"].str.contains(
                "|".join(violent_crimes), na=False
            )
        )
        property_count = sum(
            zip_data_lower["crime_type_lower"].str.contains(
                "|".join(property_crimes), na=False
            )
        )
        other_count = total_incidents - violent_count - property_count

        stats["crime_severity_analysis"] = {
            "violent_crimes": violent_count,
            "property_crimes": property_count,
            "other_crimes": other_count,
            "violent_crime_percentage": (
                round((violent_count / total_incidents) * 100, 2)
                if total_incidents > 0
                else 0
            ),
            "property_crime_percentage": (
                round((property_count / total_incidents) * 100, 2)
                if total_incidents > 0
                else 0
            ),
        }

        return stats

    def get_recent_crimes_with_geos(self):
        """
        Extract all records with Point geometries in 2025
        """
        columns = [
            "crime_category",
            "premise_type",
            "zip_code",
            "occurred_on",
            "geometry",
        ]

        # Filter columns
        df = self.crime_2025[columns]

        # Filter out missing geometry records
        df = df[df.geometry.notna()]

        return df
