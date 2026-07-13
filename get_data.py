
import requests           # the key API Python library
from pprint import pprint # Pretty Print
import time               # measuring the length of time between different items being run

import pandas as pd
import ast

import os
from dotenv import load_dotenv
load_dotenv()
SKIDDLE_API_KEY = os.getenv('SKIDDLE_API_KEY')
TM_API_KEY = os.getenv('TICKETMASTER_API_KEY')


print('hello')

import requests
import time
import pandas as pd

# used AI to create a function that retrieves the Ticketmaster data for three keywords: fest, festival and open air.
# (I created a function for one keyword, then expanded it with AI to include all functions)
def ticketmaster_festivals(api_key):
    base_url = "https://app.ticketmaster.com/discovery/v2/events.json"
    keywords = ['fest', 'festival', 'open air']
    all_data_frames = []
    
    for kw in keywords:
        print(f"Fetching data for keyword: '{kw}'...")
        params = {
            "countryCode": "GB",
            "segmentName": "Music",
            "keyword": kw,
            "apikey": api_key,
            "size": 50
        }
        
        keyword_events = []
        current_page = 0
        
        while True:
            params["page"] = current_page
            response = requests.get(base_url, params=params)
            
            if response.status_code != 200:
                break
                
            data = response.json()
            if "_embedded" in data:
                keyword_events.extend(data["_embedded"]["events"])
            
            page_info = data.get("page", {})
            if current_page >= page_info.get("totalPages", 1) - 1:
                break
            
            current_page += 1
            time.sleep(0.5)
            
        if keyword_events:
            all_data_frames.append(pd.json_normalize(keyword_events))
            
    # Combine all dataframes
    if all_data_frames:
        combined_df = pd.concat(all_data_frames, ignore_index=True)
        # Remove duplicates based on the 'id' column
        final_df = combined_df.drop_duplicates(subset=['id'])
        return final_df
    else:
        return pd.DataFrame()

# Import API key and create dataframe
api_key = TM_API_KEY
df = ticketmaster_festivals(TM_API_KEY)

# Extract the relevant columns
tm_data = pd.DataFrame()
tm_data['event_name'] = df['name']
tm_data['date'] = df['dates.start.localDate']

# Convert start datetime string to datetime object
tm_data['start_datetime'] = pd.to_datetime(df['dates.start.dateTime'], utc=True)

# Convert end datetime string to datetime object
tm_data['end_datetime'] = pd.to_datetime(df['dates.end.dateTime'], utc=True)

# Fill missing start_datetime and end_datetime with values from 'date'
tm_data['start_datetime'] = tm_data['start_datetime'].fillna(df['dates.start.localDate'])
tm_data['end_datetime'] = tm_data['end_datetime'].fillna(df['dates.start.localDate'])

# Extract the venue name from the _embedded.venues column
tm_data['venue_name'] = df['_embedded.venues'].apply(
    lambda x: x[0].get('name') if isinstance(x, list) and len(x) > 0 else None
)

# Extract the postalCode from the _embedded.venues column
tm_data['postalCode'] = df['_embedded.venues'].apply(
    lambda x: x[0].get('postalCode') if isinstance(x, list) and len(x) > 0 else None
)

# Save the extracted data to a new CSV file
tm_data.to_csv('cleaned_ticketmaster_data5.csv', index=False)


# function to get the skiddle data.
# AI was used for this function
def skiddle_festivals(api_key):
    url = "https://www.skiddle.com/api/v1/events/search/"
    all_events = []
    limit = 100  # Request max allowed per call
    offset = 0
    
    while True:
        params = {
            'api_key': api_key,
            'country': 'GB',
            'eventcode': 'FEST',
            'limit': limit,
            'offset': offset,
            'description': 1
        }
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        events = data.get('results', [])
        if not events:
            break
            
        all_events.extend(events)
        
        # Check if we've received fewer events than the limit, 
        # meaning we've reached the end of the results
        if len(events) < limit:
            break
            
        offset += limit
        time.sleep(0.1) # Good practice to avoid hitting rate limits too hard
        
    return pd.DataFrame(all_events)

# retrieving the data
skiddle = skiddle_festivals(SKIDDLE_API_KEY)

# AI used for readability: Grouping columns by logic helps understand why they are being removed
index_based_drops = skiddle.columns[:7].tolist()

cancellation_cols = [
    'cancellationDate', 'cancellationType', 'cancellationReason'
]
media_cols = [
    'imageurl', 'largeimageurl', 'xlargeimageurl', 'xlargeimageurlWebP'
]
metadata_cols = [
    'link', 'openingtimes', 'minage', 'imgoing', 'goingtos', 'goingtocount',
    'tickets', 'ticketpricing', 'entryprice', 'eventvisibility', 'ticketUrl',
    'hotSeller', 'rep', 'headerHex', 'currency', 'artists', 'genres',
    'healthAndSafety', 'festivalId'
]

columns_to_remove = index_based_drops + cancellation_cols + media_cols + metadata_cols

# Perform the drop
skiddle.drop(columns=columns_to_remove, inplace=True, errors='ignore')

# AI used: extract the relevant data from venue into its own columns
# AI used: extract the relevant data from venue into its own columns
def extract_venue_fields(row_data):
    # If it's already a dictionary (which is expected from the JSON response)
    if isinstance(row_data, dict):
        data = row_data
    # If it somehow got converted to a string, parse it
    elif isinstance(row_data, str):
        try:
            data = ast.literal_eval(row_data)
        except (ValueError, SyntaxError):
            data = {}
    # Fallback for missing/NaN values
    else:
        data = {}
        
    return pd.Series({
        'venue_name': data.get('name'),
        'postcode':   data.get('postcode'),
        'longitude':  data.get('longitude'),
        'latitude':   data.get('latitude')
    })

venue_details = skiddle['venue'].apply(extract_venue_fields)

# Add the new columns to the main dataframe
skiddle = pd.concat([skiddle, venue_details], axis=1)

# Remove the original 'venue' column as it is no longer needed
skiddle.drop(columns=['venue'], inplace=True)

#convert the date columns to datetime
skiddle['date'] = pd.to_datetime(skiddle['date'])
skiddle['rescheduledDate'] = pd.to_datetime(skiddle['rescheduledDate'])

#drop rows where cancelled = 1 and there is no data in the rescheduledDate
skiddle.drop(skiddle[(skiddle['cancelled'] == 1) & (skiddle['rescheduledDate'].isna())].index, inplace=True)
skiddle.drop(columns=['cancelled'], inplace=True)

skiddle['startdate'] = pd.to_datetime(skiddle['startdate'])
skiddle['enddate'] = pd.to_datetime(skiddle['enddate'])

#replace the date with the rescheduled date, if there is a rescheduled date
skiddle['date'] = skiddle['rescheduledDate'].fillna(skiddle['date'])
skiddle.drop(columns=['rescheduledDate'], inplace=True) 


#drop the description column, longitude and latitude columns and the festival column
skiddle.drop(columns=['description', 'festival','longitude','latitude'], inplace=True)

#save to csv
#skiddle.to_csv('cleaned_skiddle_data10.csv', index=False)

#combining the datasets into one dataset, then cleaning it
# 1. Load the datasets
skiddle_df = skiddle
ticketmaster_df = tm_data

# 2. Standardize column names for easier merging
skiddle_df = skiddle_df.rename(columns={'eventname': 'event_name', 'postcode': 'venue_postcode'})
ticketmaster_df = ticketmaster_df.rename(columns={'postalCode': 'venue_postcode'})

# 3. Combine the dataframes
combined_df = pd.concat([skiddle_df, ticketmaster_df], ignore_index=True)

# This uses the 'start_datetime' if available, otherwise falls back to 'startdate'
combined_df['start'] = combined_df['start_datetime'].fillna(combined_df['startdate'])
combined_df['end'] = combined_df['end_datetime'].fillna(combined_df['enddate'])

# 5. Clean up: Drop the original, redundant columns
final_df = combined_df.drop(columns=['startdate', 'enddate', 'start_datetime', 'end_datetime'])

# We drop duplicates based on the event name, venue, and the newly created 'start' time
final_df = final_df.drop_duplicates(subset=['event_name', 'venue_name', 'start'])
final_df = final_df.drop_duplicates(subset=['start', 'end', 'venue_postcode'])
final_df = final_df.drop_duplicates(subset=['event_name', 'venue_postcode'])

#AI used: skiddle api suddenly sent dates in different format 
final_df['date'] = pd.to_datetime(final_df['date'], format='%Y-%m-%d', errors='coerce')

# 7. Save to a new file
final_df.to_csv('final_merged_events8.csv', index=False)

print(f"Merge successful! Total unique entries: {len(final_df)}")
print(final_df.head())
