from pathlib import Path
import streamlit as st
from utils.styles import apply_sidebar_styles
import pandas as pd
from datetime import datetime
from collect_data import DataCollector, DataCleaner, run_data_pipeline
from data_cleaner import AdvancedDataCleaner
from gap_analyser import EventGapAnalyser, analyse_events_gap
from festival_opportunity import FestivalOpportunityAnalyzer
from external_factors import ExternalFactorsAnalyzer, OpportunityFinder
import os
from dotenv import load_dotenv  # ADD THIS
import folium
from streamlit_folium import folium_static, st_folium
import plotly.express as px

# Load environment variables FIRST
load_dotenv()

# Apply sidebar styles
# apply_sidebar_styles()

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

# Initialise session states
if "events_df" not in st.session_state:
    st.session_state.events_df = None
if "quality_df" not in st.session_state:
    st.session_state.quality_df = None
if "gaps_df" not in st.session_state:
    st.session_state.gaps_df = None
if "gap_analysis_results" not in st.session_state:
    st.session_state.gap_analysis_results = None

# Title
st.title("UK Regional Live Music Data")
st.markdown("*Download, clean and analyse data from Skiddle and Ticketmaster*")

# Configure sidebar
with st.sidebar:
    st.header("Data Management")
    st.markdown("---")
    st.header("Data Collection")

    # # Check API keys - FIXED logic
    # if SKIDDLE_API_KEY and SKIDDLE_API_KEY not in [
    #     "SKIDDLE_API_KEY",
    #     "your_skiddle_api_key_here",
    #     "",
    #     None,
    # ]:
    #     st.success("✅ Skiddle API Key: Configured")
    # else:
    #     st.error("❌ Skiddle API Key: Missing or invalid")

    # if TICKET_API_KEY and TICKET_API_KEY not in [
    #     "TICKET_API_KEY",
    #     "your_ticketmaster_api_key_here",
    #     "",
    #     None,
    # ]:
    #     st.success("✅ Ticketmaster API Key: Configured")
    # else:
    #     st.error("❌ Ticketmaster API Key: Missing or invalid")

    # # Debug info
    # if not SKIDDLE_API_KEY or SKIDDLE_API_KEY in [
    #     "SKIDDLE_API_KEY",
    #     "your_skiddle_api_key_here",
    #     "",
    #     None,
    # ]:
    #     st.warning("⚠️ Skiddle key not found. Check your .env file")

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
        fetch_button = st.button(
            "Fetch & Clean Data", type="primary", width="stretch"
        )  # Changed width
    with col2:
        load_button = st.button("Load Latest Data", width="stretch")  # Changed width

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
        None,
    ]:
        st.error("❌ Skiddle API Key is missing or invalid. Check your .env file")
        return None

    if not ticketmaster_key or ticketmaster_key in [
        "TICKET_API_KEY",
        "your_ticketmaster_api_key_here",
        "",
        None,
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
        width="stretch",
    )

    # Tabs for different views
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
        [
            "🗺️ Map View",
            "📊 Analysis",
            "📈 Density",
            "📋 Data Preview",
            # "ℹ️ Quality Report",
            "📆 Event Gap Analysis",
            # "🔍 Gap Investigation & Opportunity Finder",
            "🎪 Festival Opportunity",
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

        st_folium(m, width=800, height=500)

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
            st.plotly_chart(fig, width="stretch")

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
            st.plotly_chart(fig, width="stretch")

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
            st.plotly_chart(fig, width="stretch")

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
                st.plotly_chart(fig, width="stretch")
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
            st.plotly_chart(fig, width="stretch")

            # Show data table
            st.subheader("Regional Metrics")
            st.dataframe(
                region_filtered.sort_values("events_per_100k", ascending=False),
                width="stretch",
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
            width="stretch",
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
                    width="stretch",
                )

    # with tab5:
    #     st.subheader("ℹ️ Data Quality Report")

    #     if "quality_score" in df.columns:
    #         col1, col2 = st.columns(2)

    #         with col1:
    #             # Quality distribution
    #             quality_dist = df["quality_score"].value_counts().sort_index()
    #             fig = px.bar(
    #                 x=quality_dist.index,
    #                 y=quality_dist.values,
    #                 title="Quality Score Distribution",
    #                 labels={"x": "Quality Score", "y": "Number of Events"},
    #                 color=quality_dist.values,
    #                 color_continuous_scale="Viridis",
    #             )
    #             fig.update_layout(showlegend=False)
    #             st.plotly_chart(fig, width="stretch")

    #         with col2:
    #             # Quality by source
    #             quality_by_source = (
    #                 df.groupby("source")["quality_score"].mean().reset_index()
    #             )
    #             fig = px.bar(
    #                 quality_by_source,
    #                 x="source",
    #                 y="quality_score",
    #                 title="Average Quality Score by Source",
    #                 color="quality_score",
    #                 color_continuous_scale="Viridis",
    #             )
    #             fig.update_layout(showlegend=False)
    #             st.plotly_chart(fig, width="stretch")

    #         # Quality breakdown
    #         st.subheader("Quality Breakdown by Category")
    #         quality_breakdown = (
    #             df.groupby("event_category")["quality_score"]
    #             .agg(["mean", "count"])
    #             .reset_index()
    #         )
    #         quality_breakdown.columns = ["Category", "Avg Quality", "Count"]
    #         st.dataframe(
    #             quality_breakdown.sort_values("Avg Quality", ascending=False),
    #             width="stretch",
    #             hide_index=True,
    #         )

    with tab5:
        st.subheader("📆 Event Gap Analysis")
        st.markdown("*Find periods with no events and analyse potential causes*")

        if "date_parsed" not in df.columns:
            df["date_parsed"] = pd.to_datetime(df["date"], errors="coerce")

        # Gap analysis
        col1, col2 = st.columns(2)

        with col1:
            gap_threshold = st.slider(
                "Minimum days without events to consider a gap",
                min_value=1,
                max_value=14,
                value=3,
                help="Events with no events for this many consecutive days are considered gaps",
            )

        with col2:
            # Date range
            if not df["date_parsed"].isna().all():
                min_date = df["date_parsed"].min().date()
                max_date = df["date_parsed"].max().date()

                date_range = st.date_input(
                    "Date range for analysis",
                    value=(min_date, max_date),
                    min_value=min_date,
                    max_value=max_date,
                )

        # Run gap analysis
        if st.button("Find Event Gaps"):
            with st.spinner("Analysing event gaps..."):
                # Filter by date range
                if date_range and len(date_range) == 2:
                    start_date, end_date = date_range
                    filtered_df = df[
                        (df["date_parsed"] >= pd.to_datetime(start_date))
                        & (df["date_parsed"] <= pd.to_datetime(end_date))
                    ]
                else:
                    filtered_df = df

                # Run analysis
                analyser = EventGapAnalyser(filtered_df)
                gaps = analyser.find_gaps(gap_threshold)
                summary = analyser.get_gap_summary(gap_threshold)
                causes = analyser.analyze_gap_causes(gaps)

                if gaps.empty:
                    st.success("No significant gaps found! Events are well distributed")
                else:
                    # Display summary
                    st.subheader("📊 Gap Summary")

                    col1, col2, col3, col4 = st.columns(4)

                    with col1:
                        st.metric("Total Gaps", summary["total_gaps"])
                    with col2:
                        st.metric("Total Gap Days", summary["total_gap_days"])
                    with col3:
                        st.metric(
                            "Average Gap", f"{summary['average_gap_days']:.1f} days"
                        )
                    with col4:
                        st.metric("Largest Gap", f"{summary['max_gap_days']} days")

                    # Display largest gap
                    if summary["largest_gap"]:
                        largest = summary["largest_gap"]
                        st.warning(
                            f"⚠️ **Largest Gap**: {largest['gap_days']} days from {largest['gap_start'].strftime('%Y-%m-%d')} to {largest['gap_end'].strftime('%Y-%m-%d')}"
                        )

                    # Gap timeline
                    st.subheader("📈 Gap Timeline")

                    # Create timeline visualization
                    import plotly.graph_objects as go

                    fig = go.Figure()

                    # Add events as scatter
                    events_df = filtered_df[filtered_df["date_parsed"].notna()]
                    fig.add_trace(
                        go.Scatter(
                            x=events_df["date_parsed"],
                            y=[1] * len(events_df),
                            mode="markers",
                            name="Events",
                            marker=dict(color="blue", size=8, symbol="circle"),
                            text=(
                                events_df["event_name"]
                                if "event_name" in events_df.columns
                                else None
                            ),
                            hoverinfo="text+x",
                        )
                    )

                    # Add gaps as rectangles
                    for _, gap in gaps.iterrows():
                        fig.add_vrect(
                            x0=gap["gap_start"],
                            x1=gap["gap_end"],
                            fillcolor="red",
                            opacity=0.3,
                            layer="below",
                            line_width=0,
                        )

                    fig.update_layout(
                        title="Events and Gaps Timeline",
                        xaxis_title="Date",
                        yaxis_title="",
                        yaxis=dict(showticklabels=False, range=[0.5, 1.5]),
                        height=300,
                        showlegend=False,
                    )
                    st.plotly_chart(fig, width="stretch")

                    # Show gaps table
                    st.subheader("📋 Detailed Gap List")
                    st.dataframe(
                        gaps[
                            [
                                "gap_start",
                                "gap_end",
                                "gap_days",
                                "day_of_week_start",
                                "month",
                            ]
                        ].sort_values("gap_days", ascending=False),
                        width="stretch",
                        hide_index=True,
                        column_config={
                            "gap_start": st.column_config.DateColumn("Start Date"),
                            "gap_end": st.column_config.DateColumn("End Date"),
                            "gap_days": st.column_config.NumberColumn(
                                "Days", format="%d"
                            ),
                            "day_of_week_start": "Start Day",
                            "month": "Month",
                        },
                    )

                    # Gap causes analysis
                    st.subheader("🔍 Possible Causes of Gaps")

                    if causes is None:
                        causes = {}

                    col1, col2 = st.columns(2)

                    with col1:
                        # Check if seasonal_pattern exists before accessing
                        if causes.get("seasonal_pattern"):
                            st.write("**Seasonal Patterns**")
                            if causes["seasonal_pattern"].get("most_gap_prone_month"):
                                st.write(
                                    f"Most gap-prone month: {causes['seasonal_pattern']['most_gap_prone_month']}"
                                )

                            if causes["seasonal_pattern"].get("gaps_by_month"):
                                month_df = pd.DataFrame(
                                    list(
                                        causes["seasonal_pattern"][
                                            "gaps_by_month"
                                        ].items()
                                    ),
                                    columns=["Month", "Gap Count"],
                                )
                                st.dataframe(month_df, hide_index=True)
                        else:
                            st.info("No seasonal pattern data available")

                    with col2:
                        # Check if day_pattern exists before accessing
                        if causes.get("day_pattern"):
                            st.write("**Day of Week Patterns**")
                            if causes["day_pattern"].get("most_gap_prone_day"):
                                st.write(
                                    f"Most gap-prone day: {causes['day_pattern']['most_gap_prone_day']}"
                                )

                            if causes["day_pattern"].get("gaps_by_day"):
                                day_df = pd.DataFrame(
                                    list(causes["day_pattern"]["gaps_by_day"].items()),
                                    columns=["Day", "Gap Count"],
                                )
                                st.dataframe(day_df, hide_index=True)
                        else:
                            st.info("No day pattern data available")

                    # Holiday analysis - check if exists
                    if causes.get("holiday_pattern"):
                        st.write("**Holiday/Seasonal Effects**")
                        st.write(
                            f"Gaps during holidays: {causes['holiday_pattern'].get('gaps_during_holidays', 0)}"
                        )
                        st.write(
                            f"Percentage of gaps during holidays: {causes['holiday_pattern'].get('percentage_of_gaps', 0):.1f}%"
                        )
                    else:
                        st.info("No holiday pattern data available")

                    # Download gaps data
                    csv_gaps = gaps.to_csv(index=False).encode("utf-8")
                    st.download_button(
                        label="📥 Download Gap Analysis (CSV)",
                        data=csv_gaps,
                        file_name=f"event_gaps_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv",
                    )

    # with tab6:  # New tab for gap investigation
    #     st.subheader("🔍 Gap Investigation & Opportunity Finder")
    #     st.markdown("*Analyze why gaps occur and identify opportunities to fill them*")

    #     if "date_parsed" not in df.columns:
    #         df["date_parsed"] = pd.to_datetime(df["date"], errors="coerce")

    #     # Select a gap to investigate
    #     if st.session_state.gaps_df is not None and not st.session_state.gaps_df.empty:
    #         st.markdown("### Select a Gap to Investigate")

    #         # Let user select a gap
    #         gap_options = []
    #         for idx, gap in st.session_state.gaps_df.iterrows():
    #             gap_label = f"{gap['gap_start'].strftime('%Y-%m-%d')} to {gap['gap_end'].strftime('%Y-%m-%d')} ({gap['gap_days']} days)"
    #             gap_options.append((idx, gap_label))

    #         if gap_options:
    #             selected_idx = st.selectbox(
    #                 "Choose a gap to investigate",
    #                 options=[opt[0] for opt in gap_options],
    #                 format_func=lambda x: dict(gap_options)[x],
    #             )

    #             if selected_idx is not None:
    #                 selected_gap = st.session_state.gaps_df.loc[selected_idx]

    #                 # Initialize analyzers
    #                 external_analyzer = ExternalFactorsAnalyzer()
    #                 opportunity_finder = OpportunityFinder()

    #                 # Analyze the gap
    #                 with st.spinner("Analyzing external factors..."):
    #                     # Get gap analysis
    #                     gap_analysis = external_analyzer.analyze_gap_causes(
    #                         df, selected_gap["gap_start"], selected_gap["gap_end"]
    #                     )

    #                     # Identify opportunities
    #                     opportunities = external_analyzer.identify_opportunities(
    #                         gap_analysis, df
    #                     )

    #                     # Prioritize opportunities
    #                     prioritized = opportunity_finder.prioritize_opportunities(
    #                         opportunities
    #                     )

    #                 # Display results
    #                 st.markdown("### 📊 Gap Analysis Results")

    #                 # Gap details
    #                 col1, col2, col3 = st.columns(3)
    #                 with col1:
    #                     st.metric("Gap Duration", f"{selected_gap['gap_days']} days")
    #                 with col2:
    #                     st.metric("Month", selected_gap["month"])
    #                 with col3:
    #                     st.metric("Year", selected_gap["year"])

    #                 # External Factors
    #                 st.markdown("### 🌍 External Factors Contributing to the Gap")

    #                 for factor in gap_analysis["external_factors"]:
    #                     with st.expander(
    #                         f"**{factor['type']}** - Impact: {factor['impact'].upper()}"
    #                     ):
    #                         st.write(factor["description"])
    #                         if isinstance(factor["details"], dict):
    #                             st.json(factor["details"])
    #                         elif isinstance(factor["details"], list):
    #                             for item in factor["details"]:
    #                                 if isinstance(item, dict):
    #                                     st.write(f"- {item}")
    #                                 else:
    #                                     st.write(f"- {item}")
    #                         else:
    #                             st.write(factor["details"])

    #                 # Opportunities
    #                 st.markdown("### 💡 Identified Opportunities")

    #                 if prioritized:
    #                     # Summary metrics
    #                     col1, col2, col3 = st.columns(3)
    #                     with col1:
    #                         high_priority = len(
    #                             [
    #                                 o
    #                                 for o in prioritized
    #                                 if o["priority_level"] == "High"
    #                             ]
    #                         )
    #                         st.metric("High Priority Opportunities", high_priority)
    #                     with col2:
    #                         medium_priority = len(
    #                             [
    #                                 o
    #                                 for o in prioritized
    #                                 if o["priority_level"] == "Medium"
    #                             ]
    #                         )
    #                         st.metric("Medium Priority Opportunities", medium_priority)
    #                     with col3:
    #                         low_priority = len(
    #                             [o for o in prioritized if o["priority_level"] == "Low"]
    #                         )
    #                         st.metric("Low Priority Opportunities", low_priority)

    #                     # Display opportunities
    #                     for idx, opp in enumerate(prioritized):
    #                         with st.expander(
    #                             f"{idx+1}. {opp['type']} - Priority: {opp['priority_level']} (Score: {opp['priority_score']}/10)"
    #                         ):
    #                             st.write(f"**Description**: {opp['description']}")
    #                             st.write(
    #                                 f"**Target Audience**: {opp['target_audience']}"
    #                             )
    #                             st.write(
    #                                 f"**Potential Venues**: {opp['potential_venues']}"
    #                             )
    #                             st.write(f"**Suggestion**: {opp['suggestion']}")

    #                     # Export opportunities
    #                     opp_df = pd.DataFrame(prioritized)
    #                     csv_opp = opp_df.to_csv(index=False).encode("utf-8")
    #                     st.download_button(
    #                         label="📥 Download Opportunities (CSV)",
    #                         data=csv_opp,
    #                         file_name=f"opportunities_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
    #                         mime="text/csv",
    #                     )
    #                 else:
    #                     st.info("No specific opportunities identified for this gap.")

    #                 # Recommendations
    #                 st.markdown("### 🎯 Recommendations")

    #                 recs = [
    #                     "Consider reaching out to local venues to fill the gap",
    #                     "Look for promoters who might be available during this period",
    #                     "Check if there are any community events that could be organized",
    #                     "Consider virtual events as an alternative",
    #                     "Partner with local businesses for event sponsorship",
    #                 ]

    #                 # Add specific recommendations based on gap type
    #                 if selected_gap["gap_days"] >= 7:
    #                     recs.append(
    #                         "📅 **Weekly Event Series**: Consider establishing a weekly event series to prevent recurring gaps"
    #                     )

    #                 if selected_gap["month"] in ["1", "2"]:
    #                     recs.append(
    #                         "❄️ **Winter Events**: January/February gaps can be filled with indoor concerts, comedy nights, or theater productions"
    #                     )

    #                 if selected_gap["month"] in ["7", "8"]:
    #                     recs.append(
    #                         "🏖️ **Summer Events**: These months are ideal for outdoor events - consider pop-up concerts or mini-festivals"
    #                     )

    #                 for rec in recs:
    #                     st.write(f"- {rec}")

    #                 # Additional research suggestions
    #                 st.markdown("### 🔬 Suggested Further Research")
    #                 st.info("""
    #                 **To understand these gaps better:**
    #                 1. Check local venue availability during these periods
    #                 2. Contact event promoters about their scheduling challenges
    #                 3. Survey potential attendees about what events they would attend
    #                 4. Research other cities' event schedules for comparison
    #                 5. Look at transportation/travel patterns during these periods
    #                 """)

    #     else:
    #         st.info(
    #             "No gaps found to investigate. Try adjusting the gap threshold or date range."
    #         )

    with tab6:  # After your existing tabs
        st.subheader("🎪 Festival Opportunity Finder")
        st.markdown("*Identify where and when a new mid-sized festival could succeed*")

        if (
            st.session_state.events_df is not None
            and not st.session_state.events_df.empty
        ):
            df = st.session_state.events_df

            # Initialize analyzer
            with st.spinner("Analyzing festival opportunities..."):
                # Make sure we have regions data
                if regions_df is not None and not regions_df.empty:
                    analyzer = FestivalOpportunityAnalyzer(df, regions_df)

                    # Get opportunities
                    opportunities = analyzer.identify_festival_opportunities()

                    # Display recommendations
                    st.markdown("### ⭐ Top Festival Recommendations")

                    # Show top 3 recommendations as cards
                    recs = opportunities.get("recommendations", [])
                    if recs:
                        for rec in recs[:3]:
                            with st.container():
                                col1, col2 = st.columns([3, 1])
                                with col1:
                                    st.markdown(
                                        f"**{rec['priority']}. {rec['title']}**"
                                    )
                                    st.markdown(f"_{rec['description'].strip()}_")
                                with col2:
                                    if rec["rating"] == "High":
                                        st.success(f"⭐ {rec['rating']}")
                                    elif rec["rating"] == "Medium":
                                        st.warning(f"⭐ {rec['rating']}")
                                    else:
                                        st.info(f"⭐ {rec['rating']}")
                                    st.metric("Score", f"{rec['score']:.0f}/100")
                                st.divider()

                    # 2. Region opportunity map
                    st.markdown("### 🗺️ Region Opportunity Map")
                    plots = analyzer.create_visualizations()
                    if "opportunity_map" in plots:
                        st.plotly_chart(plots["opportunity_map"], width="stretch")

                    # 3. Density analysis
                    st.markdown("### 📊 Event Density by Region")

                    col1, col2 = st.columns(2)

                    with col1:
                        # Show density chart
                        if "density_chart" in plots:
                            st.plotly_chart(plots["density_chart"], width="stretch")

                    with col2:
                        # Show opportunity regions table
                        region_opp = opportunities.get(
                            "region_opportunities", pd.DataFrame()
                        )
                        if not region_opp.empty:
                            st.dataframe(
                                region_opp[
                                    [
                                        "region",
                                        "event_count",
                                        "population",
                                        "events_per_100k",
                                        "opportunity_rating",
                                    ]
                                ],
                                width="stretch",
                                hide_index=True,
                                column_config={
                                    "region": "Region",
                                    "event_count": "Events",
                                    "population": "Population",
                                    "events_per_100k": "Events per 100k",
                                    "opportunity_rating": "Opportunity",
                                },
                            )

                    # 4. Calendar gap analysis
                    st.markdown("### 📅 Calendar Gap Analysis")

                    col1, col2 = st.columns(2)

                    with col1:
                        calendar = opportunities.get("calendar_gaps", {})
                        if calendar.get("best_gap_for_festival"):
                            gap = calendar["best_gap_for_festival"]
                            st.info(f"""
                            **Ideal Festival Window**
                            - Dates: {gap['start'].strftime('%Y-%m-%d')} to {gap['end'].strftime('%Y-%m-%d')}
                            - Duration: {gap['duration_days']} days
                            - Season: {gap['season']}
                            - Month: {gap['month']}
                            """)

                        # Show month gaps
                        if calendar.get("months_with_most_gaps"):
                            st.write("**Months with Most Gaps:**")
                            for month, count in list(
                                calendar["months_with_most_gaps"].items()
                            )[:5]:
                                st.write(f"- {month}: {count} gaps")

                    with col2:
                        # Show gap timeline
                        if "gap_timeline" in plots:
                            st.plotly_chart(plots["gap_timeline"], width="stretch")

                    # 5. Genre analysis
                    st.markdown("### 🎵 Genre Gap Analysis")

                    genre_data = opportunities.get("genre_opportunities", {})
                    if genre_data:
                        # Create genre gap summary
                        genre_summary = []
                        for region, data in genre_data.items():
                            if data and data.get("underserved_genres"):
                                for g in data["underserved_genres"][:3]:
                                    genre_summary.append(
                                        {
                                            "Region": region,
                                            "Genre": g["genre"],
                                            "Events": g["count"],
                                            "Percentage": f"{g['percentage']:.1f}%",
                                            "Potential": (
                                                "High"
                                                if g["percentage"] < 5
                                                else "Medium"
                                            ),
                                        }
                                    )

                        if genre_summary:
                            genre_df = pd.DataFrame(genre_summary)
                            st.dataframe(
                                genre_df,
                                width="stretch",
                                hide_index=True,
                                column_config={
                                    "Region": "Region",
                                    "Genre": "Genre",
                                    "Events": "Events",
                                    "Percentage": "% of Events",
                                    "Potential": "Potential",
                                },
                            )

                    # 6. Download report
                    st.markdown("### 📋 Festival Opportunity Report")

                    if st.button("Generate Full Report"):
                        report = analyzer.generate_festival_report()
                        st.text_area("Festival Opportunity Report", report, height=400)

                        # Download button
                        st.download_button(
                            label="📥 Download Report",
                            data=report,
                            file_name=f"festival_opportunity_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                            mime="text/plain",
                        )

        else:
            st.info(
                "👈 Please load or fetch data first to analyze festival opportunities."
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
