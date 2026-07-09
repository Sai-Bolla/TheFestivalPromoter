import streamlit as st
import pandas as pd
import requests
import os
import plotly.express as px
from dotenv import load_dotenv

load_dotenv()


API_KEY = os.getenv("SKIDDLE_API_KEY")
BASE_URL = "https://www.skiddle.com/api/v1/events/search/"

st.set_page_config(page_title="Skiddle data exploring", layout="wide")
st.title("🎶 Skiddle data")

st.sidebar.header("Search Filters")
latitude = st.sidebar.number_input("Latitude", value=53.4839, format="%.4f")
longitude = st.sidebar.number_input("Longitude", value=-2.2446, format="%.4f")
radius = st.sidebar.number_input("Radius (miles)", min_value=1, max_value=50, value=5)
event_code = st.sidebar.selectbox(
    "Event Type",
    options=[
        "FEST",
        "LIVE",
        "CLUB",
        "THEATRE",
        "COMEDY",
        "EXHIB",
        "KIDS",
        "SPORT",
        "ARTS",
    ],
    index=1,  # Default to 'LIVE'
)


# Functions to get data
@st.cache_data(ttl=3600)  # Cache data for 1 hour
def fetch_events(api_key, lat, lon, rad, code):
    params = {
        "api_key": API_KEY,
        "latitude": lat,
        "longitude": lon,
        "radius": rad,
        "eventcode": code,
        "description": 1,
        "order": "date",
        "limit": 50,
    }

    try:
        response = requests.get(BASE_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data.get("results", [])  # Return list of events
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching data: {e}")
        return []


if st.sidebar.button("Search Events"):
    if not API_KEY or API_KEY == "API_KEY":
        st.error("Please replace your api key with the correct one.")
        st.stop()
    with st.spinner("Fetching events"):
        events = fetch_events(API_KEY, latitude, longitude, radius, event_code)

    if events:

        # Convert to dataframe
        df = pd.DataFrame(events)

        if "venue" in df.columns:
            df["venue_name"] = df["venue"].apply(
                lambda x: x.get("name", "N/A") if isinstance(x, dict) else "N/A"
            )
            df["venue_town"] = df["venue"].apply(
                lambda x: x.get("town", "N/A") if isinstance(x, dict) else "N/A"
            )

        #   The 'description' column is a list of dicts like [{'type': 'Genre', 'content': 'Rock'}]
        def extract_genre(desc_list):
            if isinstance(desc_list, list):
                for item in desc_list:
                    if isinstance(item, dict) and item.get("type") == "Genre":
                        return item.get("content", "Other")
            return "Other"

        if "description" in df.columns:
            df["primary_genre"] = df["description"].apply(extract_genre)

        # 3. Select and rename columns for display
        columns_to_show = [
            "id",
            "eventname",
            "venue_name",
            "venue_town",
            "primary_genre",
            "date",
            "tickets_available",
            "link",
        ]
        # Keep only columns that exist
        final_columns = [col for col in columns_to_show if col in df.columns]
        display_df = df[final_columns].copy()
        display_df.rename(
            columns={
                "id": "Event ID",
                "eventname": "Event Name",
                "venue_name": "Venue",
                "venue_town": "Town/City",
                "primary_genre": "Genre",
                "date": "Date",
                "tickets_available": "Tickets Available?",
                "link": "URL",
            },
            inplace=True,
        )

        # --- Visualize in Streamlit ---
        st.subheader(f"Found {len(display_df)} Events")

        # Display DataFrame
        st.dataframe(display_df, use_container_width=True, hide_index=True)

        # --- Visualization: Chart of Events by Genre ---
        if not display_df.empty and "Genre" in display_df.columns:
            genre_counts = display_df["Genre"].value_counts().reset_index()
            genre_counts.columns = ["Genre", "Count"]

            fig = px.bar(
                genre_counts,
                x="Genre",
                y="Count",
                title="Number of Events by Genre",
                color="Genre",
                color_discrete_sequence=px.colors.qualitative.Pastel,
            )
            st.plotly_chart(fig, use_container_width=True)
            
        if not display_df.empty and 'venue_town' in display_df.columns:
            # Top venues chart
            top_venues = display_df['Venue'].value_counts().head(10).reset_index()
            top_venues.columns = ['Venue', 'Event Count']
            fig2 = px.bar(top_venues, x='Venue', y='Event Count', 
                        title='Top 10 Venues by Events')
            st.plotly_chart(fig2, use_container_width=True)

                # Optional: Show a map of the events (if you have latitude/longitude)
                # ... (See Notes Below)

    else:
        st.warning("No events found. Try adjusting the filters.")
