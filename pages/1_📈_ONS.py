import streamlit as st
import requests
import json
import pandas as pd
from datetime import datetime

# from dotenv import load_dotenv


BASE_URL = "https://api.beta.ons.gov.uk/v1"
POPULATION_ENDPOINT = "datasets"

st.set_page_config(page_title="ONS API Explorer", layout="wide")

# Custom CSS for better styling
st.markdown(
    """
    <style>
    .stButton button {
        width: 100%;
    }
    .dataset-card {
        padding: 10px;
        border-radius: 5px;
        border: 1px solid #ddd;
        margin: 5px 0;
    }
    </style>
""",
    unsafe_allow_html=True,
)


def find_population_dataset():
    """Fetches the published index and finds a dataset related to population."""
    url = f"{BASE_URL}/{POPULATION_ENDPOINT}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        # Search through the index for 'population' in the title or description
        # The exact structure of the index may vary, so you might need to explore the JSON
        if isinstance(data, list):
            for item in data:
                if "population" in str(item.get("title", "")).lower():
                    return item.get("id")
        elif isinstance(data, dict):
            # Some APIs wrap the list in a key like 'items' or 'results'
            for key in ["items", "results", "datasets"]:
                if key in data and isinstance(data[key], list):
                    for item in data[key]:
                        if "population" in str(item.get("title", "")).lower():
                            return item.get("id")
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None


# Example usage
dataset_id = find_population_dataset()
if dataset_id:
    print(f"Found dataset ID: {dataset_id}")
    # Now fetch the actual data
    data_url = f"https://api.beta.ons.gov.uk/v1/api/data/{dataset_id}"
    print(f"Fetch data from: {data_url}")
else:
    print("No population dataset found. Check the publishedindex response structure.")


@st.cache_data(ttl=3600)  # cache data for an hour
def fetch_people_data(subpath=""):
    endpoint = (
        f"{POPULATION_ENDPOINT}/{subpath.lstrip('/')}"
        if subpath
        else POPULATION_ENDPOINT
    )
    url = f"{BASE_URL}/{endpoint}"

    try:
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching data: {e}")
        return None
    except json.JSONDecodeError:
        st.error("Error decoding JSON response.")
        return None


@st.cache_data(ttl=3600)
def fetch_dataset_details(dataset_path):
    data = fetch_people_data(dataset_path)
    return data


def extract_datasets_from_data(data,current_path=""):
    datasets = []

    if not data:
        return datasets

    def traverse(obj, path):
        if isinstance(obj, dict):
            # is it a dataset
            if "id" in obj or "title" in obj or "name" in obj:
                dataset_info = {
                    "id": obj.get("id", obj.get("name", "unknown")),
                    "title": obj.get("title", obj.get("name", "Untitled dataset")),
                    "description": obj.get(
                        "description", obj.get("summary", "No description available")
                    ),
                    "path": path,
                    "type": obj.get("type", "dataset"),
                    "release_date": obj.get(
                        "releaseDate", obj.get("publishedDate", "Unknown")
                    ),
                }
                datasets.append(dataset_info)

            for key, value in obj.items():
                traverse(value, f"{path}/{key}" if path else key)
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                traverse(item, f"{path}[{i}]")

    traverse(data, current_path)
    return datasets


def display_dataset_info(dataset_data, dataset_path):
    """Displays detailed dataset information for people/population data."""
    if not dataset_data:
        st.warning("No detailed data available for this dataset.")
        return

    # Create tabs for different aspects
    tabs = st.tabs(
        ["📊 Overview", "📋 Data Preview", "📈 Population Statistics", "🔍 Raw JSON"]
    )

    with tabs[0]:
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Dataset Information")
            # Display key fields
            key_fields = [
                "id",
                "title",
                "name",
                "description",
                "summary",
                "abstract",
                "subject",
            ]
            for field in key_fields:
                if field in dataset_data and dataset_data[field]:
                    st.write(
                        f"**{field.replace('_', ' ').title()}:** {dataset_data[field]}"
                    )

            # Display path
            st.write(f"**Path:** `{dataset_path}`")

        with col2:
            st.subheader("Time & Coverage")
            # Display time-related fields
            time_fields = [
                "releaseDate",
                "publishedDate",
                "created",
                "updated",
                "period",
                "timePeriod",
            ]
            for field in time_fields:
                if field in dataset_data and dataset_data[field]:
                    st.write(
                        f"**{field.replace('_', ' ').title()}:** {dataset_data[field]}"
                    )

            # Geographic coverage
            if "geographicCoverage" in dataset_data:
                st.write(
                    f"**Geographic Coverage:** {dataset_data['geographicCoverage']}"
                )
            if "geographicGranularity" in dataset_data:
                st.write(
                    f"**Geographic Granularity:** {dataset_data['geographicGranularity']}"
                )

    with tabs[1]:
        st.subheader("Data Preview")
        # Try to display data in a tabular format
        if "data" in dataset_data and isinstance(dataset_data["data"], list):
            try:
                df = pd.DataFrame(dataset_data["data"])
                st.dataframe(df.head(20))
                st.caption(f"Showing first 20 rows of {len(df)} total rows")
            except Exception as e:
                st.write("Could not display data as table. Showing raw data:")
                st.json(
                    dataset_data["data"][:5]
                    if isinstance(dataset_data["data"], list)
                    else dataset_data["data"]
                )
        elif "observations" in dataset_data and isinstance(
            dataset_data["observations"], list
        ):
            try:
                df = pd.DataFrame(dataset_data["observations"])
                st.dataframe(df.head(20))
            except Exception:
                st.json(dataset_data["observations"][:5])
        elif "population" in dataset_data and isinstance(
            dataset_data["population"], list
        ):
            try:
                df = pd.DataFrame(dataset_data["population"])
                st.dataframe(df.head(20))
            except Exception:
                st.json(dataset_data["population"][:5])
        else:
            st.info(
                "No tabular data preview available. Check the Raw JSON tab for complete data."
            )

    with tabs[2]:
        st.subheader("Population & Community Statistics")
        # Look for population-specific data
        if isinstance(dataset_data, dict):
            # Try to identify population statistics
            pop_indicators = [
                "population",
                "births",
                "deaths",
                "migration",
                "age",
                "gender",
                "ethnicity",
                "households",
                "families",
                "marriage",
                "divorce",
                "lifeExpectancy",
            ]

            found_stats = False
            for indicator in pop_indicators:
                if indicator in dataset_data:
                    found_stats = True
                    st.write(f"**{indicator.replace('_', ' ').title()}:**")
                    if isinstance(dataset_data[indicator], dict):
                        st.json(dataset_data[indicator])
                    elif isinstance(dataset_data[indicator], list):
                        st.write(f"Found {len(dataset_data[indicator])} entries")
                        try:
                            df = pd.DataFrame(dataset_data[indicator][:10])
                            st.dataframe(df)
                        except:
                            st.json(dataset_data[indicator][:5])
                    else:
                        st.write(dataset_data[indicator])

            if not found_stats:
                st.info("No specific population statistics found in this dataset.")

            # Show dimension information
            if "dimensions" in dataset_data:
                st.subheader("Data Dimensions")
                st.json(dataset_data["dimensions"])

    with tabs[3]:
        st.subheader("Raw JSON Data")
        st.json(dataset_data)


# --- Streamlit App UI ---
st.set_page_config(page_title="ONS Population & Community Data Explorer", layout="wide")

# Custom CSS
st.markdown(
    """
    <style>
    .stButton button {
        width: 100%;
    }
    .dataset-card {
        padding: 10px;
        border-radius: 5px;
        border: 1px solid #ddd;
        margin: 5px 0;
    }
    .stat-box {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
    }
    </style>
""",
    unsafe_allow_html=True,
)

st.title("👥 ONS Population & Community Data Explorer")
st.markdown("""
    ### Specialized explorer for people, population, and community statistics
    *Data sourced from the Office for National Statistics `/peoplepopulationandcommunity` endpoint*
""")

# --- Sidebar: Navigation ---
st.sidebar.header("📊 Population Data Navigator")

# Main navigation options
nav_option = st.sidebar.radio(
    "Choose a view:",
    [
        "📂 Browse All Population Data",
        "🔍 Search Datasets",
        "📈 Key Population Indicators",
        "🔧 Direct Path Navigation",
    ],
)

# --- Initialize session state ---
if "selected_dataset" not in st.session_state:
    st.session_state["selected_dataset"] = None
if "selected_path" not in st.session_state:
    st.session_state["selected_path"] = None

# --- Main Content ---
if nav_option == "📂 Browse All Population Data":
    st.header("📂 Population & Community Data Structure")
    st.write(
        "Browse through the hierarchical structure of population and community datasets."
    )

    # Fetch the root people data
    with st.spinner("Loading population data structure..."):
        people_data = fetch_people_data()

    if people_data:
        # Extract datasets from the structure
        datasets = extract_datasets_from_data(people_data)

        if datasets:
            st.success(f"Found {len(datasets)} datasets in the population category")

            # Display in a tree-like structure
            def display_dataset_tree(data, level=0):
                if isinstance(data, dict):
                    # Check if this is a leaf node (dataset)
                    if "id" in data or "title" in data:
                        dataset_id = data.get("id", data.get("name", "unknown"))
                        dataset_title = data.get("title", data.get("name", "Untitled"))

                        # Create a card for each dataset
                        with st.container():
                            col1, col2 = st.columns([4, 1])
                            with col1:
                                st.write(f"{'  ' * level}📊 **{dataset_title}**")
                                if "description" in data:
                                    st.caption(
                                        f"{'  ' * level}{data['description'][:150]}..."
                                    )
                            with col2:
                                if st.button(
                                    "View Details", key=f"browse_{dataset_id}_{level}"
                                ):
                                    # Store the full path
                                    st.session_state["selected_dataset"] = dataset_id
                                    st.session_state["selected_path"] = dataset_id
                                    st.rerun()

                    # Recursively display children
                    for key, value in data.items():
                        if key not in ["id", "title", "name", "description", "summary"]:
                            display_dataset_tree(value, level + 1)

                elif isinstance(data, list):
                    for item in data:
                        display_dataset_tree(item, level + 1)

            # Display the tree
            display_dataset_tree(people_data)

        else:
            st.info(
                "No datasets found in the population category. Try exploring sub-categories."
            )
    else:
        st.error("Failed to load population data structure.")

elif nav_option == "🔍 Search Datasets":
    st.header("🔍 Search Population & Community Datasets")

    # Fetch the root data for searching
    with st.spinner("Loading dataset index..."):
        people_data = fetch_people_data()

    if people_data:
        datasets = extract_datasets_from_data(people_data)

        if datasets:
            # Search interface
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                search_term = st.text_input(
                    "Search datasets:", placeholder="e.g., population, birth, census..."
                )
            with col2:
                filter_type = st.selectbox(
                    "Filter by:",
                    [
                        "All",
                        "Population",
                        "Births",
                        "Deaths",
                        "Migration",
                        "Households",
                    ],
                )
            with col3:
                sort_by = st.selectbox(
                    "Sort by:", ["Relevance", "Title", "Release Date"]
                )

            # Filter datasets
            filtered_datasets = datasets
            if search_term:
                search_lower = search_term.lower()
                filtered_datasets = [
                    d
                    for d in datasets
                    if search_lower in d["title"].lower()
                    or search_lower in d["description"].lower()
                    or search_lower in d["id"].lower()
                ]

            # Apply category filter
            if filter_type != "All":
                filtered_datasets = [
                    d
                    for d in filtered_datasets
                    if filter_type.lower() in d["title"].lower()
                    or filter_type.lower() in d["description"].lower()
                    or filter_type.lower() in d["id"].lower()
                ]

            # Sort datasets
            if sort_by == "Title":
                filtered_datasets.sort(key=lambda x: x["title"])
            elif sort_by == "Release Date":
                filtered_datasets.sort(
                    key=lambda x: x.get("release_date", ""), reverse=True
                )

            if not filtered_datasets:
                st.warning("No datasets match your search criteria.")
            else:
                st.write(f"Found {len(filtered_datasets)} matching datasets")

                # Display results in a grid
                for i, dataset in enumerate(filtered_datasets):
                    with st.expander(f"📊 {dataset['title']}", expanded=False):
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.write(f"**ID:** `{dataset['id']}`")
                            st.write(f"**Description:** {dataset['description']}")
                            if dataset.get("release_date"):
                                st.write(f"**Release Date:** {dataset['release_date']}")
                            st.caption(f"**Path:** {dataset['path']}")
                        with col2:
                            if st.button(
                                "View Details", key=f"search_{dataset['id']}_{i}"
                            ):
                                st.session_state["selected_dataset"] = dataset["id"]
                                st.session_state["selected_path"] = dataset["path"]
                                st.rerun()
        else:
            st.info("No datasets available to search.")
    else:
        st.error("Failed to load data for searching.")

elif nav_option == "📈 Key Population Indicators":
    st.header("📈 Key Population Indicators")
    st.write("Quick access to major population and community statistics.")

    # Define common population indicators
    indicators = {
        "Population Estimates": "populationestimates",
        "Births": "births",
        "Deaths": "deaths",
        "Migration": "migration",
        "Households": "households",
        "Families": "families",
        "Marriage & Divorce": "marriage",
        "Life Expectancy": "lifeexpectancy",
        "Census 2021": "census",
        "Demographics": "demographics",
    }

    col1, col2 = st.columns(2)
    indicator_options = list(indicators.keys())

    for i, (indicator_name, indicator_path) in enumerate(indicators.items()):
        with col1 if i % 2 == 0 else col2:
            with st.container():
                st.markdown(f"**{indicator_name}**")
                if st.button(
                    f"Explore {indicator_name}", key=f"indicator_{indicator_path}"
                ):
                    st.session_state["selected_path"] = indicator_path
                    st.session_state["selected_dataset"] = indicator_path
                    st.rerun()

    st.divider()
    st.info(
        "💡 Tip: These are common population indicators. Use the search or browse features to find more specific datasets."
    )

elif nav_option == "🔧 Direct Path Navigation":
    st.header("🔧 Direct Path Navigation")
    st.write(
        "Navigate directly to a specific path within the `/peoplepopulationandcommunity` structure."
    )

    # Show current path
    st.caption(f"Base path: `/{POPULATION_ENDPOINT}`")

    # Input for path
    path_input = st.text_input(
        "Enter sub-path (e.g., 'births', 'populationestimates', or 'census/2021'):",
        placeholder="Type a path to explore...",
        value=st.session_state.get("selected_path", ""),
    )

    if st.button("Go to Path", type="primary"):
        if path_input:
            st.session_state["selected_path"] = path_input
            st.session_state["selected_dataset"] = path_input
            st.rerun()

    # Display quick links
    st.subheader("Popular Paths")
    popular_paths = [
        "populationestimates",
        "births",
        "deaths",
        "migration",
        "households",
        "families",
        "census/2021",
        "demographics",
    ]

    # Display as buttons in a grid
    cols = st.columns(4)
    for i, path in enumerate(popular_paths):
        with cols[i % 4]:
            if st.button(f"📁 {path}", key=f"quick_{path}"):
                st.session_state["selected_path"] = path
                st.session_state["selected_dataset"] = path
                st.rerun()

# --- Dataset Detail View (shown when a dataset is selected) ---
if st.session_state.get("selected_dataset") and st.session_state.get("selected_path"):
    st.divider()

    # Display breadcrumb
    st.subheader(f"📊 Dataset: {st.session_state['selected_dataset']}")
    st.caption(f"Path: `/{POPULATION_ENDPOINT}/{st.session_state['selected_path']}`")

    # Fetch and display dataset details
    with st.spinner(f"Loading dataset '{st.session_state['selected_dataset']}'..."):
        dataset_details = fetch_dataset_details(st.session_state["selected_path"])

    if dataset_details:
        display_dataset_info(dataset_details, st.session_state["selected_path"])

        # Close button
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button("Close Dataset", width="stretch"):
                st.session_state["selected_dataset"] = None
                st.session_state["selected_path"] = None
                st.rerun()
    else:
        st.warning(
            f"Could not fetch details for the selected dataset. The path '/{POPULATION_ENDPOINT}/{st.session_state['selected_path']}' might not exist or might not contain a dataset."
        )
        if st.button("Clear Selection"):
            st.session_state["selected_dataset"] = None
            st.session_state["selected_path"] = None
            st.rerun()

# --- Footer ---
st.sidebar.markdown("---")
st.sidebar.caption("👥 Population & Community Data Explorer")
st.sidebar.caption(f"Working with: `/{POPULATION_ENDPOINT}`")
st.sidebar.caption("Data sourced from Office for National Statistics")
