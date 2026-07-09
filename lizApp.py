import streamlit as st
import requests
import os
from dotenv import load_dotenv
import pandas as pd
from datetime import datetime

load_dotenv()

TICKET_API_KEY = os.getenv("TICKET_API_KEY")
BASE_URL = "https://app.ticketmaster.com/discovery/v2/events.json?"
# EVENTS_ENDPOINT = f"apikey={TICKET_API_KEY}"
# COUNTRY_ENDPOINT = f"countryCode=GB&apikey={TICKET_API_KEY}"


st.set_page_config(page_title="Ticketmaster UK Events", page_icon="🏷️", layout="wide")

COLORS = {
    "primary": "#1A3A8F",  # Dark blue - main headings, primary elements
    "secondary": "#6B35C8",  # Purple - buttons, highlights
    "accent": "#00B4C8",  # Teal - accents, hover effects
    "dark": "#0D1F5C",  # Navy - sidebar, footer, borders
    "light_purple": "#C8B8F0",  # Light purple - backgrounds, cards
    "background": "#F4F4F6",  # Light gray - page background
}

st.markdown(
    """
<style>
    .stApp {{        
        background-color: #f0faf2;
    }}
    
    # .main .block-container {{
    #     padding-top: 2rem;
    #     padding-bottom: 2rem;
    # }}
    
    # h1, h2, h3 {{
    #     color: {COLORS['primary']} !Important;
    # }}
    
    # h1 {{
    #     border-bottom: 3px solid {COLORS['secondary']};
    #     padding-bottom: 0.5rem;
    # }}
    
    # .stButton > button {{
    #     background: linear-gradient(135deg, {COLORS['primary']}, {COLORS['secondary']}) !important;
    #     color: white !important;
    #     font-weight: bold !important;
    #     border: none !important;
    #     border-radius: 8px !important;
    #     padding: 0.6rem 1.2rem !important;
    #     transition: all 0.3s ease !important;
    #     box-shadow: 0 2px 8px rgba(26, 58, 143, 0.3);
    }}
</style>
""",
    unsafe_allow_html=True,
)

# Title and description
st.title("🎫 Ticketmaster UK Events")
st.markdown("Finding a gap in events in the UK")


def extract_event_date(event):
    dates = event.get("dates", {})

    # Standard date
    start = dates.get("start", {})
    if start.get("localDate"):
        return start.get("localDate")

    # Date range
    if dates.get("start", {}).get("localDate"):
        return dates["start"]["localDate"]

    # Span
    if dates.get("span", {}).get("localDate"):
        return dates["span"]["localDate"]

    # Status
    if dates.get("status", {}).get("localDate"):
        return dates["status"]["localDate"]

    # Embedded date
    if event.get("_embedded", {}).get("dates", {}).get("localDate"):
        return event["_embedded"]["dates"]["localDate"]

    # Sale dates
    if dates.get("access", {}).get("localDate"):
        return dates["access"]["localDate"]

    return "N/A"


def extract_event_time(event):
    dates = event.get("dates", {})
    start = dates.get("start", {})

    if start.get("localTime"):
        return start.get("localTime")

    # Check if there's a time in the date field
    if start.get("localDate") and "T" in start.get("localDate", ""):
        # If it's a full datetime string, extract the time part
        try:
            # Format: "2026-07-15T19:30:00" -> "19:30"
            time_part = start["localDate"].split("T")[1][:5]
            return time_part
        except:
            pass

    # Check if there's a timezone or other time field
    if start.get("dateTime"):
        try:
            # If there's a dateTime field, extract time
            time_part = start["dateTime"].split("T")[1][:5]
            return time_part
        except:
            pass

    # missing time
    return "TBC"


# Sidebar
with st.sidebar:
    st.header("**🔍 Search Filters**")
    city = st.text_input("City", placeholder="e.g., London, Manchester")
    keyword = st.text_input("Keyword", placeholder="e.g., Taylor Swift, Jay-Z")
    classification = st.selectbox(
        "Category",
        options=["All", "Music", "Sports", "Arts & Theatre", "Family", "Comedy"],
        index=0,
    )

    # Date range
    st.markdown("**📅 Date Range**")
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input(
            "Start Date", value=None, help="Leave blank for no filter"
        )
    with col2:
        end_date = st.date_input(
            "End Date", value=None, help="Leave blank for no filter"
        )

    # Number of results
    size = st.slider(
        "Number of results per page", min_value=5, max_value=100, value=20, step=5
    )

    st.markdown("---")

    show_raw = st.checkbox("Show raw API data (debug)", value=False)

    # Search button
    search_button = st.button("🔍 Search Events", type="primary", width="stretch")

if search_button:
    # if not TICKET_API_KEY:
    #     st.error("❌ Please enter your Ticketmaster API key")
    #     st.stop()
    with st.spinner("Fetching events from Ticketmaster..."):
        try:
            params = {
                "apikey": TICKET_API_KEY,
                "countryCode": "GB",
                "size": size,
                "sort": "date,asc",
            }

            # Optional filters
            if city:
                params["city"] = city
            if keyword:
                params["keyword"] = keyword
            if classification and classification != "All":
                params["classificationName"] = classification.lower()
            if start_date:
                params["startDateTime"] = start_date.strftime("%Y-%m-%dT00:00:00Z")
            if end_date:
                params["endDateTime"] = end_date.strftime("%Y-%m-%dT23:59:59Z")

            # API request
            response = requests.get(BASE_URL, params=params, timeout=30)
            data = response.json()

            # check respoonse
            if response.status_code != 200:
                st.error(f"❌ API Error: {data.get('message', 'Unknown error')}")
                st.stop()

            # Get events
            events = data.get("_embedded", {}).get("events", [])

            if not events:
                st.warning(
                    "☹️ No events found matching your criteria.  Try adjusting your filters"
                )
                st.stop()

            # Display total
            if show_raw:
                with st.expander("🔍 Raw API Response (first event)"):
                    st.json(events[0] if events else {})

            total_elements = data.get("page", {}).get("totalElements", len(events))
            st.success(f"✅ Found {total_elements} events (showing {len(events)})")

            event_data = []

            # Process events
            for e in events:
                # Venue information
                venues = e.get("_embedded", {}).get("venues", [])
                venue_name = venues[0].get("name", "N/A") if venues else "N/A"
                venue_city = (
                    venues[0].get("city", {}).get("name", "N/A") if venues else "N/A"
                )

                # Date information
                event_date = extract_event_date(e)
                event_time = extract_event_time(e)

                # Classification (genre)
                classifications = e.get("classifications", [])
                genre = (
                    classifications[0].get("genre", {}).get("name", "N/A")
                    if classifications
                    else "N/A"
                )

                # Get url
                event_url = e.get("url", "#")

                # Show full date
                dates = e.get("dates", {})
                start = dates.get("start", {})
                date_status = dates.get("status", {})
                date_span = dates.get("span", {})

                event_data.append(
                    {
                        "ID": e.get("id", "N/A"),
                        "Event Name": e.get("name", "N/A"),
                        "Venue": venue_name,
                        "City": venue_city,
                        "Date": event_date,
                        "Time": event_time,
                        "Genre": genre,
                        "Ticket URL": event_url,
                        # Debugging
                        "_date_debug": {
                            "start": start,
                            "status": date_status,
                            "span": date_span,
                        },
                    }
                )

            # Display as DataFrame
            df = pd.DataFrame(event_data)

            # Debug information for dates
            if show_raw:
                with st.expander("📊 Date Extraction Debug"):
                    date_status_counts = df[df["Date"] != "N/A"].shape[0]
                    st.write(f"Events with dates: {date_status_counts}/{len(df)}")
                    st.write("Sample dates:", df["Date"].head(10).tolist())

            # Show summary
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Events", len(df))
            with col2:
                unique_venues = df["Venue"].nunique()
                st.metric("Unique Venues", unique_venues)
            with col3:
                unique_cities = df["City"].nunique()
                st.metric("Cities", unique_cities)

            # Display interactive table
            st.subheader("📋 Event List")

            # Display only the visible columns
            display_columns = [
                "ID",
                "Event Name",
                "Venue",
                "City",
                "Date",
                "Time",
                "Genre",
                "Ticket URL",
            ]

            display_df = df[display_columns]

            # Add filters for the table
            st.dataframe(
                df,
                width="stretch",
                hide_index=True,
                column_config={
                    "ID": st.column_config.TextColumn("Event ID", width="small"),
                    "Event Name": st.column_config.TextColumn(
                        "Event Name", width="medium"
                    ),
                    "Venue": st.column_config.TextColumn("Venue", width="medium"),
                    "City": st.column_config.TextColumn("City", width="small"),
                    "Date": st.column_config.TextColumn("Date", width="small"),
                    "Time": st.column_config.TextColumn("Time", width="small"),
                    "Genre": st.column_config.TextColumn("Genre", width="small"),
                    "Ticket URL": st.column_config.LinkColumn(
                        "Buy Tickets", width="small"
                    ),
                },
            )

            # --- Display as cards (alternative view) ---
            st.subheader("🃏 Event Cards")

            # Create columns for card layout (3 per row)
            cols_per_row = 3
            for i in range(0, len(event_data), cols_per_row):
                cols = st.columns(cols_per_row)
                for j in range(cols_per_row):
                    idx = i + j
                    if idx < len(event_data):
                        event = event_data[idx]
                        with cols[j]:
                            with st.container(border=True):
                                st.markdown(f"### 🎵 {event['Event Name']}")
                                st.markdown(f"**📍 Venue:** {event['Venue']}")
                                st.markdown(f"**🏙️ City:** {event['City']}")
                                st.markdown(f"**📅 Date:** {event['Date']}")
                                st.markdown(f"**⏰ Time:** {event['Time']}")
                                st.markdown(f"**🎭 Genre:** {event['Genre']}")

                                # Buy tickets button
                                if event["Ticket URL"] != "#":
                                    st.link_button(
                                        "🎟️ Buy Tickets",
                                        event["Ticket URL"],
                                        width="stretch",
                                    )
                                else:
                                    st.button(
                                        "🔒 Tickets Unavailable",
                                        disabled=True,
                                        width="stretch",
                                    )

            # --- Option to download as CSV ---
            csv = df.to_csv(index=False)
            st.download_button(
                label="📥 Download as CSV",
                data=csv,
                file_name=f"ticketmaster_events_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                width="stretch",
            )

        except requests.exceptions.RequestException as e:
            st.error(f"❌ Network error: {str(e)}")
        except Exception as e:
            st.error(f"❌ An error occurred: {str(e)}")
else:
    # Show welcome message
    st.info("Search filters in sidebar, then click 'Search Events'")
