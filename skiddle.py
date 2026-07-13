import streamlit as st

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


'''
 country code: GB
    
    ID 	Market
    202 	London (UK)
    203 	South (UK)
    204 	Midlands and Central (UK)
    205 	Wales and North West (UK)
    206 	North and North East (UK)
    207 	Scotland
    208 	Ireland
    209 	Northern Ireland

    dmaId 	Market

    601 	All of United Kingdom
    602 	London
    603 	South
    604 	Midlands and Central
    605 	Wales and North West
    606 	North and North East
    607 	Scotland
    608 	All of Ireland
    609 	Northern Ireland

previous URLs:

https://app.ticketmaster.com/discovery/v2/events.json?classificationName=music&dmaId=324&apikey=BoAGsXs6gY0DExT82C1VQopCVBBDT7uj


'''


import requests
import time
import pandas as pd

'''

def get_combined_festivals_df(api_key):
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

# Usage
api_key = 'BoAGsXs6gY0DExT82C1VQopCVBBDT7uj'
df = get_combined_festivals_df(api_key)
print(f"Final count after removing duplicates: {len(df)}")


st.dataframe(df)
'''

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
API_KEY = SKIDDLE_API_KEY
skiddle = skiddle_festivals(API_KEY)

# Grouping columns by logic helps understand why they are being removed
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
skiddle.to_csv('cleaned_skiddle_data15.csv', index=False)

print(skiddle.columns.tolist())
print(skiddle.head())
print(skiddle.info())
print(skiddle.dtypes)


