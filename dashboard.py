import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import numpy as np

# Page configuration
st.set_page_config(page_title="Summer Events Dashboard", layout="wide")

st.title("🎪 Summer Events Dashboard")
st.subheader("Busiest Weekends: June - August 2026")

# Load the data
@st.cache_data
def load_data():
    df = pd.read_csv('final_merged_events8.csv')
    # Use dayfirst=True if your CSV saves dates as DD/MM/YYYY
    df['date'] = pd.to_datetime(df['date'], dayfirst=True, errors='coerce')
    df['start'] = pd.to_datetime(df['start'], dayfirst=True, errors='coerce')
    df['end'] = pd.to_datetime(df['end'], dayfirst=True, errors='coerce')
    return df

try:
    df = load_data()
    
    # Filter for June, July, August
    summer_df = df[df['date'].dt.month.isin([6, 7, 8])].copy()
    
    # Add day of week (0=Monday, 5=Saturday, 6=Sunday)
    summer_df['day_of_week'] = summer_df['date'].dt.dayofweek
    summer_df['day_name'] = summer_df['date'].dt.day_name()
    
    # Filter for weekends only (Saturday=5, Sunday=6)
    # Filter for weekends only (Saturday=5, Sunday=6)
    weekend_df = summer_df[summer_df['day_of_week'].isin([5, 6])].copy()
    
    # 1. Generate the week_start anchor (Make sure this runs first!)
    weekend_df['week_start'] = weekend_df['date'] - pd.to_timedelta(
        weekend_df['date'].dt.dayofweek - 5, unit='d'
    )
    
    # 2. Group by weekend and count the events
    weekend_events = weekend_df.groupby('week_start').agg({
        'event_name': 'count'
    }).reset_index()
    
    # 3. Flatten and rename the columns safely
    weekend_events.columns = ['week_start', 'event_count']
    
    # 4. Explicitly map out the full Sat-Sun range mathematically
    weekend_events['first_date'] = weekend_events['week_start']
    weekend_events['last_date'] = weekend_events['week_start'] + pd.to_timedelta(1, unit='d')
    
    # 5. Sort by busiest weekends
    weekend_events = weekend_events.sort_values('event_count', ascending=False)
    
    # Display key metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Summer Events (Weekends)", len(weekend_df))
    with col2:
        st.metric("Busiest Weekend Events", int(weekend_events['event_count'].max()))
    with col3:
        st.metric("Average Events per Weekend", f"{weekend_events['event_count'].mean():.1f}")
    
    st.divider()
    
    # Display top busiest weekends
    st.subheader("🔥 Top 10 Busiest Weekends")
    
    top_weekends = weekend_events.head(10).copy()
    
    # Added , %Y to the second date format to display the year
    top_weekends['weekend_dates'] = top_weekends.apply(
        lambda x: f"{x['first_date'].strftime('%a, %b %d')} - {x['last_date'].strftime('%a, %b %d, %Y')}", 
        axis=1
    )
    
    # Create a table view
    display_df = top_weekends[['weekend_dates', 'event_count']].copy()
    display_df.columns = ['Weekend Dates', 'Number of Events']
    display_df = display_df.reset_index(drop=True)
    display_df.index = display_df.index + 1
    
    st.dataframe(display_df, use_container_width=True)
    
    st.divider()
    
    # Visualization: Bar chart of top 10 weekends
    st.subheader("📊 Event Distribution")
    
    fig, ax = plt.subplots(figsize=(12, 6))
    
    top_10 = weekend_events.head(10).copy()
    top_10['label'] = top_10.apply(
        lambda x: f"{x['first_date'].strftime('%b %d')}-{x['last_date'].strftime('%d')}", 
        axis=1
    )
    
    colors = plt.cm.viridis(np.linspace(0.3, 0.9, len(top_10)))
    bars = ax.barh(range(len(top_10)), top_10['event_count'], color=colors)
    
    ax.set_yticks(range(len(top_10)))
    ax.set_yticklabels(top_10['label'])
    ax.set_xlabel('Number of Events', fontsize=11, fontweight='bold')
    ax.set_title('Top 10 Busiest Weekends (June - August 2026)', fontsize=13, fontweight='bold', pad=20)
    ax.invert_yaxis()
    
    # Add value labels on bars
    for i, (bar, val) in enumerate(zip(bars, top_10['event_count'])):
        ax.text(val + 0.2, i, str(int(val)), va='center', fontweight='bold')
    
    ax.grid(axis='x', alpha=0.3)
    plt.tight_layout()
    
    st.pyplot(fig)
    
    st.divider()

    st.subheader('Comparing Saturdays to Sundays')

    # Convert date column to datetime
    df['date'] = pd.to_datetime(df['date'])
    
    # Extract day of week (0=Monday, 6=Sunday)
    df['day_of_week'] = df['date'].dt.dayofweek
    df['day_name'] = df['date'].dt.day_name()
    
    # Filter for weekend days (Saturday=5, Sunday=6)
    weekend_df = df[df['day_of_week'].isin([5, 6])].copy()
    
    # Count events by day of week for weekends
    weekend_counts = weekend_df['day_name'].value_counts().sort_index()
    
    # Create a proper structure for bar chart (Saturday and Sunday)
    days = ['Saturday', 'Sunday']
    counts = [weekend_counts.get(day, 0) for day in days]
    
    # Create the bar chart
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Create bar chart with colors
    colors = ['#FF6B6B', '#4ECDC4']
    bars = ax.bar(days, counts, color=colors, edgecolor='black', linewidth=1.5, alpha=0.8)
    
    # Add value labels on top of bars
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{int(height)}',
                ha='center', va='bottom', fontsize=14, fontweight='bold')
    
    ax.set_title('Number of Events by Weekend Day', fontsize=16, fontweight='bold', pad=20)
    ax.set_xlabel('Day of Week', fontsize=12)
    ax.set_ylabel('Number of Events', fontsize=12)
    ax.set_ylim(0, max(counts) * 1.1)  # Add some space at the top
    
    plt.tight_layout()
    plt.savefig('/mnt/user-data/outputs/weekend_heatmap.png', dpi=300, bbox_inches='tight')
    print("Heatmap saved to weekend_heatmap.png")
    
    # Print summary statistics
    print("\n" + "="*50)
    print("WEEKEND EVENTS SUMMARY")
    print("="*50)
    for day in days:
        count = weekend_counts.get(day, 0)
        print(f"{day}: {count} events")
    print("="*50)
    print(f"Total weekend events: {len(weekend_df)}")

    
    
except FileNotFoundError:
    st.error("❌ Data file 'final_merged_events6.csv' not found. Please ensure it's in the same directory.")
except Exception as e:
    st.error(f"❌ An error occurred: {str(e)}")
