from datetime import datetime
from pathlib import Path
from typing import Optional
import requests
import pandas as pd
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class DataCollector:
    """Save data from APIs"""

    def __init__(
        self, skiddle_key: Optional[str] = None, 
        ticketmaster_key: Optional[str] = None, 
        data_dir: str = "data"
    ):
        # Use provided keys or fall back to environment variables
        self.skiddle_key = skiddle_key or os.getenv("SKIDDLE_API_KEY")
        self.ticketmaster_key = ticketmaster_key or os.getenv("TICKET_API_KEY")
        
        # Validate keys are present
        if not self.skiddle_key:
            print("⚠️ Warning: SKIDDLE_API_KEY not found in environment variables")
        if not self.ticketmaster_key:
            print("⚠️ Warning: TICKET_API_KEY not found in environment variables")
        
        self.data_dir = Path(data_dir)
        self.raw_dir = self.data_dir / "raw"
        self.processed_dir = self.data_dir / "processed"

        # Create folders
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.processed_dir.mkdir(parents=True, exist_ok=True)

    def fetch_skiddle_events(
        self,
        latitude: float,
        longitude: float,
        radius: int = 20,
        eventcode: str = "LIVE",
        limit: int = 200,
    ) -> pd.DataFrame:
        """Get events from Skiddle API"""
        if not self.skiddle_key:
            print("❌ Skiddle API key not configured")
            return pd.DataFrame()
            
        url = "https://www.skiddle.com/api/v1/events/search/"
        params = {
            "api_key": self.skiddle_key,
            "latitude": latitude,
            "longitude": longitude,
            "radius": radius,
            "eventcode": eventcode,
            "order": "date",
            "description": "1",
            "limit": limit,
            "getdistance": "1",
        }

        try:
            response = requests.get(url, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()
            events = data.get("results", [])

            if events:
                # Save raw data
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                raw_file = self.raw_dir / f"skiddle_events_raw_{timestamp}.csv"

                df = pd.DataFrame(events)
                df.to_csv(raw_file, index=False)

                print(f"✅ Saved {len(df)} Skiddle events to {raw_file}")
                return df
            else:
                print("⚠️ No Skiddle events found")
                return pd.DataFrame()

        except Exception as e:
            print(f"❌ Skiddle API Error: {str(e)}")
            return pd.DataFrame()

    def fetch_ticketmaster_events(
        self, 
        latitude: float, 
        longitude: float, 
        radius: int = 20, 
        size: int = 200
    ) -> pd.DataFrame:
        """Get events from ticketmaster"""
        if not self.ticketmaster_key:
            print("❌ Ticketmaster API key not configured")
            return pd.DataFrame()
            
        url = "https://app.ticketmaster.com/discovery/v2/events.json"
        params = {
            "apikey": self.ticketmaster_key,
            "latlong": f"{latitude},{longitude}",
            "radius": radius,
            "unit": "miles",
            "size": size,
            "sort": "date,asc",
        }

        try:
            response = requests.get(url, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()
            events = data.get("_embedded", {}).get("events", [])

            if events:
                # Save data
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                raw_file = self.raw_dir / f"ticketmaster_events_raw_{timestamp}.csv"

                df = pd.DataFrame(events)
                df.to_csv(raw_file, index=False)

                print(f"✅ Saved {len(df)} Ticketmaster events to {raw_file}")
                return df
            else:
                print("⚠️ No Ticketmaster events found")
                return pd.DataFrame()
                
        except Exception as e:
            print(f"❌ Ticketmaster API Error: {str(e)}")
            return pd.DataFrame()

    def load_latest_raw_data(self, source: Optional[str] = None) -> pd.DataFrame:
        """Load most recent raw data"""
        if source == "skiddle":
            files = list(self.raw_dir.glob("skiddle_events_raw_*.csv"))
        elif source == "ticketmaster":
            files = list(self.raw_dir.glob("ticketmaster_events_raw_*.csv"))
        else:
            files = list(self.raw_dir.glob("*_events_raw_*.csv"))

        if not files:
            print("⚠️ No raw data files found")
            return pd.DataFrame()

        # Get the most recent file
        latest_file = max(files, key=lambda f: f.stat().st_mtime)
        df = pd.read_csv(latest_file)
        print(f"📂 Loaded {len(df)} records from {latest_file.name}")
        return df


class DataCleaner:
    """Clean and deduplicate data"""

    def __init__(self, raw_data_dir: str = "data/raw"):
        self.raw_data_dir = Path(raw_data_dir)
        self.processed_data_dir = Path("data/processed")
        self.processed_data_dir.mkdir(parents=True, exist_ok=True)

    def load_and_normalise_skiddle_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normalise Skiddle event data"""
        if df.empty:
            return df

        normalised = pd.DataFrame()
        
        # FIXED: Skiddle API uses different field names
        # Check for both possible field names
        if 'eventname' in df.columns:
            normalised["event_name"] = df['eventname'].fillna('Unknown Event')
        elif 'EventName' in df.columns:
            normalised["event_name"] = df['EventName'].fillna('Unknown Event')
        else:
            normalised["event_name"] = 'Unknown Event'
        
        # Venue information - handle nested structure safely
        def get_venue_field(row, field, default):
            venue = row.get('venue', {})
            if isinstance(venue, dict):
                return venue.get(field, default)
            return default
        
        normalised["venue_name"] = df.apply(
            lambda x: get_venue_field(x, 'name', 'Unknown Venue'), axis=1
        )
        
        normalised["latitude"] = df.apply(
            lambda x: float(get_venue_field(x, 'latitude', 0)), axis=1
        )
        
        normalised["longitude"] = df.apply(
            lambda x: float(get_venue_field(x, 'longitude', 0)), axis=1
        )
        
        # Date field - Skiddle uses 'date' or 'startdate'
        if 'date' in df.columns:
            normalised["date"] = df['date'].fillna('Date TBC')
        elif 'startdate' in df.columns:
            normalised["date"] = df['startdate'].fillna('Date TBC')
        else:
            normalised["date"] = 'Date TBC'
        
        normalised["source"] = "Skiddle"
        
        # Genre - might be in different fields
        if 'genre' in df.columns:
            normalised["genre"] = df['genre'].fillna('N/A')
        else:
            normalised["genre"] = 'N/A'
        
        # Price - Skiddle uses 'minprice' or 'price'
        if 'minprice' in df.columns:
            normalised["price"] = df.apply(
                lambda x: f"£{x.get('minprice', 'TBC')}", axis=1
            )
        else:
            normalised["price"] = 'TBC'
        
        # URL/Link
        if 'link' in df.columns:
            normalised["url"] = df['link'].fillna('#')
        elif 'url' in df.columns:
            normalised["url"] = df['url'].fillna('#')
        else:
            normalised["url"] = '#'
        
        normalised["venue_id"] = df.apply(
            lambda x: get_venue_field(x, 'id', None), axis=1
        )
        normalised["event_id"] = df.get('id', None)

        return normalised

    def load_and_normalise_ticketmaster_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normalise Ticketmaster data"""
        if df.empty:
            return df

        normalised = pd.DataFrame()
        normalised["event_name"] = df.get("name", "Unknown Event").fillna("Unknown Event")

        # Get venue info
        def get_venue_info(row, field, default):
            venues = row.get("_embedded", {}).get("venues", [{}])
            if venues and isinstance(venues, list):
                venue = venues[0] if venues else {}
                if isinstance(venue, dict):
                    return venue.get(field, default)
            return default
        
        normalised["venue_name"] = df.apply(
            lambda x: get_venue_info(x, "name", "Unknown Venue"), axis=1
        )
        
        normalised["latitude"] = df.apply(
            lambda x: float(get_venue_info(x, "location", {}).get("latitude", 0)), axis=1
        )
        
        normalised["longitude"] = df.apply(
            lambda x: float(get_venue_info(x, "location", {}).get("longitude", 0)), axis=1
        )

        # Date
        normalised["date"] = df.apply(
            lambda x: x.get("dates", {}).get("start", {}).get("localDate", "Date TBC"),
            axis=1,
        )
        normalised["source"] = "Ticketmaster"

        # Extract genre
        def get_genres(event):
            classifications = event.get("classifications", [])
            genres = []
            if isinstance(classifications, list):
                for c in classifications:
                    if isinstance(c, dict):
                        genre = c.get("genre", {}).get("name")
                        if genre:
                            genres.append(genre)
            return ", ".join(genres) if genres else "N/A"

        normalised["genre"] = df.apply(get_genres, axis=1)

        # Extract price
        def get_price(event):
            price_ranges = event.get("priceRanges", [])
            if isinstance(price_ranges, list) and price_ranges:
                min_price = price_ranges[0].get("min")
                if min_price:
                    return f"£{min_price:.2f}"
            return "TBC"

        normalised["price"] = df.apply(get_price, axis=1)
        normalised["url"] = df.get("url", "#")
        normalised["venue_id"] = df.apply(
            lambda x: get_venue_info(x, "id", None), axis=1
        )
        normalised["event_id"] = df.get("id", None)

        return normalised

    def deduplicate_events(self, df: pd.DataFrame) -> pd.DataFrame:
        """Deduplicate events"""
        if df.empty:
            return df

        df_cleaned = df.copy()

        # Find duplicates
        df_cleaned = df_cleaned.drop_duplicates(
            subset=["venue_name", "venue_id", "date"], keep="first"
        )

        # Remove events without coordinates
        df_cleaned = df_cleaned[
            (df_cleaned["latitude"] != 0)
            & (df_cleaned["longitude"] != 0)
            & (df_cleaned["latitude"].notna())
            & (df_cleaned["longitude"].notna())
        ]

        # Remove venues with duplicated names
        df_cleaned = df_cleaned.drop_duplicates(
            subset=["event_name", "venue_name"], keep="first"
        )

        print(f"🔍 Deduplication: {len(df)} -> {len(df_cleaned)} events")
        return df_cleaned

    def clean_coordinates(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and validate coordinates"""
        if df.empty:
            return df

        # Make sure coordinates are within the UK
        # UK boundaries: lat 49.9 - 60.8, lon -10.5-1.8
        df = df[
            (df["latitude"].between(49.9, 60.8))
            & (df["longitude"].between(-10.5, 1.8))
        ]
        return df

    def combine_and_save(
        self, skiddle_df: pd.DataFrame, ticketmaster_df: pd.DataFrame
    ) -> pd.DataFrame:
        """Merge, clean and save"""
        print("🔄 Normalising Skiddle data")
        skiddle_norm = self.load_and_normalise_skiddle_data(skiddle_df)

        print("🔄 Normalising Ticketmaster data...")
        ticketmaster_norm = self.load_and_normalise_ticketmaster_data(ticketmaster_df)

        # Merge data
        combined = pd.concat([skiddle_norm, ticketmaster_norm], ignore_index=True)
        print(f"📊 Combined {len(combined)} events")

        # Clean and deduplicate
        print("🧹 Cleaning data...")
        combined = self.clean_coordinates(combined)
        combined = self.deduplicate_events(combined)

        # Sort by date
        combined["date_parsed"] = pd.to_datetime(combined["date"], errors="coerce")
        combined = combined.sort_values("date_parsed", ascending=True)
        combined = combined.drop("date_parsed", axis=1)

        # Save cleaned data
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = self.processed_data_dir / f"events_cleaned_{timestamp}.csv"
        combined.to_csv(output_file, index=False)

        latest_file = self.processed_data_dir / "events_cleaned_latest.csv"
        combined.to_csv(latest_file, index=False)

        print(f"✅ Saved {len(combined)} cleaned events to {output_file}")
        print(f"✅ Also saved as {latest_file}")

        # Generate summary
        self.generate_summary(combined)
        return combined

    def generate_summary(self, df: pd.DataFrame):
        """Save summary stats"""
        if df.empty:
            return

        summary = {
            "total_events": len(df),
            "unique_venues": df["venue_name"].nunique(),
            "events_by_source": df["source"].value_counts().to_dict(),
            "date_range": {"min": df["date"].min(), "max": df["date"].max()},
            "top_venues": df["venue_name"].value_counts().head(10).to_dict(),
            "top_genres": df["genre"].value_counts().head(10).to_dict(),
        }

        # Save summary
        summary_file = self.processed_data_dir / "summary_stats.json"
        import json

        with open(summary_file, "w") as f:
            json.dump(summary, f, indent=2)

        print(f"📊 Summary stats saved to {summary_file}")


# Main function
def run_data_pipeline(
    skiddle_key: str,
    ticketmaster_key: str,
    latitude: float,
    longitude: float,
    radius: int = 20,
    event_type: str = "LIVE",
):
    """Run the data pipeline"""
    collector = DataCollector(skiddle_key, ticketmaster_key)
    cleaner = DataCleaner()

    print("🎵 Starting data collection")

    # Fetch data
    print("📥 Fetching Skiddle events...")
    skiddle_df = collector.fetch_skiddle_events(latitude, longitude, radius, event_type)

    print("📥 Fetching Ticketmaster events...")
    ticketmaster_df = collector.fetch_ticketmaster_events(latitude, longitude, radius)

    if skiddle_df.empty and ticketmaster_df.empty:
        print("⚠️ No events found from either API")
        return None

    print("🧹 Cleaning and combining data")
    combined_df = cleaner.combine_and_save(skiddle_df, ticketmaster_df)

    return combined_df


if __name__ == "__main__":
    print("This module provides functions for collecting and cleaning event data")
    print("Run from app.py or import classes directly")