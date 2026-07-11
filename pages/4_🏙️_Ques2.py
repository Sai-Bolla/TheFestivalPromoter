from pathlib import Path
import streamlit as st
from utils.styles import apply_sidebar_styles
import pandas as pd
from datetime import datetime
from collect_data import DataCollector, DataCleaner, run_data_pipeline 
from data_cleaner import AdvancedDataCleaner
import os
from dotenv import load_dotenv  # ADD THIS
import folium
from streamlit_folium import folium_static
import plotly.express as px

# Load environment variables FIRST
load_dotenv()

# Apply sidebar styles
apply_sidebar_styles()

# Get directory paths
current_dir = os.path.dirname(os.path.abspath(__file__))
main_dir = os.path.dirname(current_dir)
csv_path = os.path.join(main_dir, "UK_regions.csv")

# Get API keys from environment
SKIDDLE_API_KEY = os.getenv("SKIDDLE_API_KEY")
TICKET_API_KEY = os.getenv("TICKET_API_KEY")

# Configure page - ONLY ONCE
SIDEBAR_LOGO = "images/eventintelligence-logo.png"
MAIN_ICON = "images/eventintelligence-logo.png"

if os.path.exists(SIDEBAR_LOGO):
    st.logo(SIDEBAR_LOGO, icon_image=MAIN_ICON)

# Set page config ONCE
st.set_page_config(page_title="Process Data", layout="wide")

# Initialise session state
if "events_df" not in st.session_state:
    st.session_state.events_df = None
if "quality_df" not in st.session_state:
    st.session_state.quality_df = None

# Title
st.title("UK Live Music Data")
st.markdown("*Download, clean and analyse data from Skiddle and Ticketmaster*")

# Configure sidebar
with st.sidebar:
    st.header("Data Management")
    st.markdown("---")
    st.header("Data Collection")

    # Check API keys - FIXED logic
    if SKIDDLE_API_KEY and SKIDDLE_API_KEY not in [
        "SKIDDLE_API_KEY",
        "your_skiddle_api_key_here",
        "",
        None
    ]:
        st.success("✅ Skiddle API Key: Configured")
    else:
        st.error("❌ Skiddle API Key: Missing or invalid")

    if TICKET_API_KEY and TICKET_API_KEY not in [
        "TICKET_API_KEY",
        "your_ticketmaster_api_key_here",
        "",
        None
    ]:
        st.success("✅ Ticketmaster API Key: Configured")
    else:
        st.error("❌ Ticketmaster API Key: Missing or invalid")

    # Debug info
    if not SKIDDLE_API_KEY or SKIDDLE_API_KEY in [
        "SKIDDLE_API_KEY",
        "your_skiddle_api_key_here",
        "",
        None
    ]:
        st.warning("⚠️ Skiddle key not found. Check your .env file")

    default_event_type = "LIVE"

    location = st.text_input("Location", value="Manchester")
    radius = st.slider("Search radius (miles)", 5, 100, 20)
    event_type = st.selectbox(
        "Event Type",
        ["LIVE", "FEST", "CLUB", "COMEDY", "THEATRE", "ALL"],
        index=(
            ["LIVE", "FEST", "CLUB", "COMEDY", "THEATRE", "ALL"].index(
                default_event_type
            )
            if default_event_type
            in ["LIVE", "FEST", "CLUB", "COMEDY", "THEATRE", "ALL"]
            else 0
        ),
    )
    max_events = st.slider("Max Events per API", 20, 500, 200)

    col1, col2 = st.columns(2)
    with col1:
        fetch_button = st.button("Fetch & Clean Data", type="primary", use_container_width=True)  # Changed width
    with col2:
        load_button = st.button("Load Latest Data", use_container_width=True)  # Changed width

    st.markdown("---")
    st.header("Data Cleaning Options")

    clean_names = st.checkbox("Standardise Venue Names", value=True)
    deduplicate = st.checkbox("Deduplicate Events", value=True)
    quality_filter = st.slider("Minimum Quality Score", 0, 10, 5)

    data_dir = os.getenv("DATA_DIR", "./data")
    st.markdown("---")
    st.caption(f"Data directory: {data_dir}")


@st.cache_data
def load_uk_regions():
    try:
        df = pd.read_csv(csv_path)
        return df
    except FileNotFoundError:
        st.warning("UK_regions.csv not found. Using default regions")
        # Fallback data
        data = {
            "region": [
                "Greater London",
                "West Midlands",
                "Greater Manchester",
                "West Yorkshire",
            ],
            "population": [8982000, 2944000, 2870000, 2350000],
            "lat": [51.5074, 52.475, 53.4808, 53.8008],
            "lon": [-0.1278, -1.8975, -2.2426, -1.5491],
        }
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"Error loading UK regions: {str(e)}")
        return pd.DataFrame()


regions_df = load_uk_regions()


# Get coordinates
@st.cache_data
def get_coordinates(location_name):
    from geopy.geocoders import Nominatim
    from geopy.exc import GeocoderTimedOut

    geolocator = Nominatim(user_agent="event_density_analyser")
    try:
        location = geolocator.geocode(f"{location_name}, UK")
        if location:
            return location.latitude, location.longitude
        else:
            location = geolocator.geocode(location_name)
            if location:
                return location.latitude, location.longitude
    except GeocoderTimedOut:
        st.warning("Geocoding timed out. Please try again.")
    except Exception as e:
        st.warning(f"Geocoding error: {str(e)}")
    return None, None


# Main functions
def fetch_and_clean_data():
    """Get data from both APIs"""
    # Check API keys - FIXED logic
    skiddle_key = SKIDDLE_API_KEY
    ticketmaster_key = TICKET_API_KEY

    if not skiddle_key or skiddle_key in [
        "SKIDDLE_API_KEY",
        "your_skiddle_api_key_here",
        "",
        None
    ]:
        st.error("❌ Skiddle API Key is missing or invalid. Check your .env file")
        return None

    if not ticketmaster_key or ticketmaster_key in [
        "TICKET_API_KEY",
        "your_ticketmaster_api_key_here",
        "",
        None
    ]:
        st.error("❌ Ticketmaster API Key is missing or invalid. Check your .env file")
        return None

    if not location:
        st.error("Please enter a location")
        return None

    # Get coordinates
    with st.spinner("Geocoding location..."):
        lat, lon = get_coordinates(location)
        if lat is None or lon is None:
            st.error("Could not find location")
            return None

    # Run data pipeline
    with st.spinner("Fetching and cleaning data... This may take a moment"):
        try:
            # Get raw data - FIXED method names
            collector = DataCollector(
                skiddle_key=skiddle_key, ticketmaster_key=ticketmaster_key
            )

            # FIXED: Changed to fetch_skiddle_events and fetch_ticketmaster_events
            skiddle_df = collector.fetch_skiddle_events(
                lat, lon, radius, event_type, max_events
            )
            ticketmaster_df = collector.fetch_ticketmaster_events(
                lat, lon, radius, max_events
            )

            if skiddle_df.empty and ticketmaster_df.empty:
                st.warning(
                    "No events found. Try increasing the radius or changing location."
                )
                return None

            # Clean and merge
            cleaner = DataCleaner()
            combined_df = cleaner.combine_and_save(skiddle_df, ticketmaster_df)

            # Advanced clean
            if clean_names or deduplicate:
                advanced_cleaner = AdvancedDataCleaner()

                if clean_names:
                    with st.spinner("Standardising venue names..."):
                        combined_df = advanced_cleaner.clean_venue_names(combined_df)

                combined_df = advanced_cleaner.extract_event_categories(combined_df)
                combined_df = advanced_cleaner.add_event_quality_score(combined_df)

                if deduplicate:
                    with st.spinner("Deduplicating events"):
                        combined_df = advanced_cleaner.deduplicate_with_confidence(
                            combined_df
                        )

                valid_df, invalid_df = advanced_cleaner.validate_event_data(combined_df)

                valid_df = valid_df[valid_df["quality_score"] >= quality_filter]

                # Save to session
                st.session_state.events_df = valid_df
                st.session_state.quality_df = invalid_df

                return valid_df

            # Save to session state
            st.session_state.events_df = combined_df
            return combined_df
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
            import traceback
            st.error(traceback.format_exc())
            return None


def load_latest_data():
    """Load latest cleaned data"""
    try:
        data_dir = Path(os.getenv("DATA_DIR", "./data"))
        processed_dir = data_dir / "processed"
        latest_file = processed_dir / "events_cleaned_latest.csv"

        if latest_file.exists():
            df = pd.read_csv(latest_file)
            st.session_state.events_df = df
            st.success(f"✅ Loaded {len(df)} events from saved data!")
            return df
        else:
            st.warning("No saved data found. Please fetch data first.")
            return None
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return None


# Handle button clicks
if fetch_button:
    df = fetch_and_clean_data()
    if df is not None and not df.empty:
        st.success(f"✅ Successfully fetched and cleaned {len(df)} events!")

elif load_button:
    df = load_latest_data()

# Display available data
if st.session_state.events_df is not None and not st.session_state.events_df.empty:
    df = st.session_state.events_df

    # Display summary
    st.subheader("Data summary")
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric("Total Events", len(df))
    with col2:
        st.metric("Unique Venues", df["venue_name"].nunique())
    with col3:
        skiddle_count = len(df[df["source"] == "Skiddle"])
        st.metric("Skiddle Events", skiddle_count)
    with col4:
        ticketmaster_count = len(df[df["source"] == "Ticketmaster"])
        st.metric("Ticketmaster Events", ticketmaster_count)
    with col5:
        avg_quality = df["quality_score"].mean() if "quality_score" in df.columns else 0
        st.metric("Avg Quality Score", f"{avg_quality:.1f}")

    # Download
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📥 Download Cleaned Data (CSV)",
        data=csv,
        file_name=f"events_cleaned_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv",
        use_container_width=True,
    )

    # Tabs for different views
    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        [
            "🗺️ Map View",
            "📊 Analysis",
            "📈 Density",
            "📋 Data Preview",
            "ℹ️ Quality Report",
        ]
    )

    with tab1:
        st.subheader("🗺️ Event Map")

        # Create map
        map_center = [df["latitude"].mean(), df["longitude"].mean()]
        m = folium.Map(location=map_center, zoom_start=11)

        # Add events to map
        for _, row in df.iterrows():
            # Different markers for different sources
            icon_color = "blue" if row["source"] == "Skiddle" else "red"

            # Quality indicator in popup
            quality_stars = "⭐" * min(int(row.get("quality_score", 0) / 2), 5)

            popup_text = f"""
            <b>{row['event_name']}</b><br>
            Venue: {row['venue_name']}<br>
            Date: {row['date']}<br>
            Source: {row['source']}<br>
            Quality: {quality_stars} ({row.get('quality_score', 0)}/10)
            """

            folium.Marker(
                location=[row["latitude"], row["longitude"]],
                popup=folium.Popup(popup_text, max_width=300),
                icon=folium.Icon(color=icon_color, icon="music", prefix="fa"),
            ).add_to(m)

        folium_static(m, width=800, height=500)

    with tab2:
        st.subheader("📊 Event Analysis")

        col1, col2 = st.columns(2)

        with col1:
            # Source distribution
            fig = px.pie(
                df,
                names="source",
                title="Events by Source",
                color_discrete_sequence=px.colors.qualitative.Set2,
            )
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            # Top venues
            top_venues = df["venue_name"].value_counts().head(10)
            fig = px.bar(
                x=top_venues.values,
                y=top_venues.index,
                title="Top 10 Venues",
                orientation="h",
                color=top_venues.values,
                color_continuous_scale="Viridis",
            )
            fig.update_layout(showlegend=False, height=400)
            st.plotly_chart(fig, use_container_width=True)

        # Event categories
        if "event_category" in df.columns:
            st.subheader("Event Categories")
            category_counts = df["event_category"].value_counts()
            fig = px.pie(
                values=category_counts.values,
                names=category_counts.index,
                title="Events by Category",
                color_discrete_sequence=px.colors.qualitative.Set3,
            )
            st.plotly_chart(fig, use_container_width=True)

        # Date distribution
        if "date" in df.columns:
            st.subheader("Events by Date")
            try:
                df["date_parsed"] = pd.to_datetime(df["date"], errors="coerce")
                date_counts = df["date_parsed"].value_counts().sort_index()

                fig = px.line(
                    x=date_counts.index,
                    y=date_counts.values,
                    title="Number of Events by Date",
                    labels={"x": "Date", "y": "Number of Events"},
                )
                st.plotly_chart(fig, use_container_width=True)
            except:
                pass

    with tab3:
        st.subheader("📈 Event Density by Region")

        # Calculate density
        def assign_region(lat, lon):
            min_distance = float("inf")
            assigned = "Other"

            for _, region in regions_df.iterrows():
                distance = (
                    (lat - region["lat"]) ** 2 + (lon - region["lon"]) ** 2
                ) ** 0.5
                if distance < min_distance:
                    min_distance = distance
                    assigned = region["region"]

            # Only assign if within reasonable distance (approximately 50 miles)
            if min_distance > 0.7:  # Roughly 50 miles
                assigned = "Other"
            return assigned

        df["region"] = df.apply(
            lambda row: assign_region(row["latitude"], row["longitude"]), axis=1
        )

        # Aggregate
        region_counts = df.groupby("region").size().reset_index(name="event_count")
        region_counts = region_counts.merge(
            regions_df[["region", "population"]], on="region", how="left"
        )
        region_counts["population"] = region_counts["population"].fillna(1)
        region_counts["events_per_100k"] = (
            region_counts["event_count"] / (region_counts["population"] / 100000)
        ).round(2)

        # Display
        region_filtered = region_counts[region_counts["region"] != "Other"]

        if not region_filtered.empty:
            fig = px.bar(
                region_filtered,
                x="region",
                y="events_per_100k",
                title="Events per 100,000 Population by Region",
                color="events_per_100k",
                color_continuous_scale="Viridis",
                text=region_filtered["event_count"].apply(lambda x: f"{x} events"),
            )
            fig.update_traces(textposition="outside")
            fig.update_layout(
                xaxis_title="Region",
                yaxis_title="Events per 100,000 Population",
                height=400,
            )
            st.plotly_chart(fig, use_container_width=True)

            # Show data table
            st.subheader("Regional Metrics")
            st.dataframe(
                region_filtered.sort_values("events_per_100k", ascending=False),
                use_container_width=True,
                hide_index=True,
                column_config={
                    "region": "Region",
                    "event_count": "Event Count",
                    "population": st.column_config.NumberColumn(
                        "Population", format="%d"
                    ),
                    "events_per_100k": st.column_config.NumberColumn(
                        "Events per 100k", format="%.2f"
                    ),
                },
            )
        else:
            st.info(
                "No events found in major UK regions. All events are in 'Other' regions."
            )

    with tab4:
        st.subheader("📋 Data Preview")

        # Show data with filters
        col1, col2, col3 = st.columns(3)
        with col1:
            source_filter = st.selectbox(
                "Filter by Source", ["All", "Skiddle", "Ticketmaster"]
            )
        with col2:
            if "quality_score" in df.columns:
                min_quality = st.slider("Min Quality Score", 0, 10, 5)
        with col3:
            if "event_category" in df.columns:
                categories = ["All"] + list(df["event_category"].unique())
                category_filter = st.selectbox("Filter by Category", categories)

        filtered_df = df.copy()
        if source_filter != "All":
            filtered_df = filtered_df[filtered_df["source"] == source_filter]
        if "quality_score" in df.columns:
            filtered_df = filtered_df[filtered_df["quality_score"] >= min_quality]
        if "event_category" in df.columns and category_filter != "All":
            filtered_df = filtered_df[filtered_df["event_category"] == category_filter]

        st.dataframe(
            filtered_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "event_name": "Event",
                "venue_name": "Venue",
                "date": "Date",
                "source": "Source",
                "event_category": "Category",
                "quality_score": st.column_config.NumberColumn("Quality", format="%d"),
                "url": st.column_config.LinkColumn("URL"),
                "latitude": st.column_config.NumberColumn("Lat", format="%.4f"),
                "longitude": st.column_config.NumberColumn("Lon", format="%.4f"),
            },
        )

        # Show invalid data if exists
        if (
            st.session_state.quality_df is not None
            and not st.session_state.quality_df.empty
        ):
            with st.expander(
                f"⚠️ Invalid/Filtered Events ({len(st.session_state.quality_df)})"
            ):
                st.dataframe(
                    st.session_state.quality_df[["event_name", "venue_name"]],
                    use_container_width=True,
                )

    with tab5:
        st.subheader("ℹ️ Data Quality Report")

        if "quality_score" in df.columns:
            col1, col2 = st.columns(2)

            with col1:
                # Quality distribution
                quality_dist = df["quality_score"].value_counts().sort_index()
                fig = px.bar(
                    x=quality_dist.index,
                    y=quality_dist.values,
                    title="Quality Score Distribution",
                    labels={"x": "Quality Score", "y": "Number of Events"},
                    color=quality_dist.values,
                    color_continuous_scale="Viridis",
                )
                fig.update_layout(showlegend=False)
                st.plotly_chart(fig, use_container_width=True)

            with col2:
                # Quality by source
                quality_by_source = (
                    df.groupby("source")["quality_score"].mean().reset_index()
                )
                fig = px.bar(
                    quality_by_source,
                    x="source",
                    y="quality_score",
                    title="Average Quality Score by Source",
                    color="quality_score",
                    color_continuous_scale="Viridis",
                )
                fig.update_layout(showlegend=False)
                st.plotly_chart(fig, use_container_width=True)

            # Quality breakdown
            st.subheader("Quality Breakdown by Category")
            quality_breakdown = (
                df.groupby("event_category")["quality_score"]
                .agg(["mean", "count"])
                .reset_index()
            )
            quality_breakdown.columns = ["Category", "Avg Quality", "Count"]
            st.dataframe(
                quality_breakdown.sort_values("Avg Quality", ascending=False),
                use_container_width=True,
                hide_index=True,
            )

else:
    # Initial state with instructions
    st.info("👈 Enter your search parameters and click 'Fetch & Clean Data' to start.")

    # Show environment info
    with st.expander("🔧 Environment Configuration"):
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**API Keys Status:**")
            st.write(
                f"- Skiddle: {'✅ Configured' if SKIDDLE_API_KEY and SKIDDLE_API_KEY not in ['SKIDDLE_API_KEY', 'your_skiddle_api_key_here', ''] else '❌ Missing'}"
            )
            st.write(
                f"- Ticketmaster: {'✅ Configured' if TICKET_API_KEY and TICKET_API_KEY not in ['TICKET_API_KEY', 'your_ticketmaster_api_key_here', ''] else '❌ Missing'}"
            )

        with col2:
            data_dir = os.getenv("DATA_DIR", "./data")
            st.markdown("**Directory Status:**")
            st.write(f"- Data Dir: {data_dir}")
            st.write(f"- Raw Dir: {data_dir}/raw")
            st.write(f"- Processed Dir: {data_dir}/processed")

        st.markdown("**Default Settings from .env:**")
        st.write(f"- Location: {os.getenv('DEFAULT_LOCATION', 'Manchester')}")
        st.write(f"- Radius: {os.getenv('DEFAULT_RADIUS', '20')} miles")
        st.write(f"- Event Type: {os.getenv('DEFAULT_EVENT_TYPE', 'LIVE')}")
        st.write(f"- Max Events: {os.getenv('DEFAULT_MAX_EVENTS', '200')}")