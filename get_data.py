"""
get_data.py — pulls fresh UK music event data from Ticketmaster and Skiddle,
cleans and combines both, and writes df_combined_genre.csv for the Streamlit dashboard.

Run with: python3 get_data.py
"""

import os
import time
import json
from pathlib import Path
from datetime import datetime

import requests
import pandas as pd
from dotenv import load_dotenv

# ---------------------------------------------------------------
# Setup
# ---------------------------------------------------------------
load_dotenv()
TM_API_KEY = os.getenv("TICKETMASTER_API_KEY")
SK_API_KEY = os.getenv("SKIDDLE_API_KEY")

if not TM_API_KEY:
    raise ValueError("No Ticketmaster key found — check .env has TICKETMASTER_API_KEY")
if not SK_API_KEY:
    raise ValueError("No Skiddle key found — check .env has SKIDDLE_API_KEY")

TM_BASE_URL = "https://app.ticketmaster.com/discovery/v2/events.json"
SK_BASE_URL = "https://www.skiddle.com/api/v1/events/search/"
RAW_DIR = Path("data/raw")
RAW_DIR.mkdir(parents=True, exist_ok=True)


# =================================================================
# GENRE BUCKET MAPPING — shared vocabulary across both sources
# =================================================================
GENRE_BUCKET_MAP = {
    'Alternative': 'Rock/Indie', 'Alternative Rock': 'Rock/Indie', 'Alternative Pop': 'Rock/Indie',
    'Adult Alternative Pop/Rock': 'Rock/Indie', 'Blues-Rock': 'Rock/Indie', 'Classic Rock': 'Rock/Indie',
    'Garage Rock': 'Rock/Indie', 'German Rock': 'Rock/Indie', 'Glam': 'Rock/Indie', 'Grunge': 'Rock/Indie',
    'Hard Rock': 'Rock/Indie', 'Indie Pop': 'Rock/Indie', 'Indie Rock': 'Rock/Indie', 'Indie': 'Rock/Indie',
    'Nu Indie': 'Rock/Indie', 'Pop Rock': 'Rock/Indie', 'Progressive Rock': 'Rock/Indie',
    'Psychedelic': 'Rock/Indie', 'Rock': 'Rock/Indie', 'Rock & Roll': 'Rock/Indie',
    'Rock & Roll / 1950s': 'Rock/Indie', 'Brit Pop': 'Rock/Indie', 'New Wave': 'Rock/Indie',
    'Post Rock': 'Rock/Indie', 'Shoegaze': 'Rock/Indie',

    'Pop': 'Pop', 'Adult Contemporary': 'Pop', 'Dream Pop': 'Pop', 'J-pop': 'Pop', 'K-pop': 'Pop',
    'Synth Pop': 'Pop',

    'Hip-Hop/Rap': 'Hip-Hop/Urban', 'Hip Hop': 'Hip-Hop/Urban', 'British Rap': 'Hip-Hop/Urban',
    'R&B': 'Hip-Hop/Urban', 'Rap': 'Hip-Hop/Urban', 'Rap-Rock': 'Hip-Hop/Urban', 'Latin Rap': 'Hip-Hop/Urban',
    'Trap': 'Hip-Hop/Urban', 'Urban': 'Hip-Hop/Urban', 'Grime': 'Hip-Hop/Urban',

    'Amapiano': 'Electronic/Dance', 'Ambient': 'Electronic/Dance', 'Club Dance': 'Electronic/Dance',
    'Dance Pop': 'Electronic/Dance', 'Dance/Electronic': 'Electronic/Dance', 'Disco': 'Electronic/Dance',
    'Electro Pop': 'Electronic/Dance', 'Electro-Jazz': 'Electronic/Dance', 'Electronic': 'Electronic/Dance',
    'House': 'Electronic/Dance', 'New Age': 'Electronic/Dance', 'Techno': 'Electronic/Dance',
    'Acid House': 'Electronic/Dance', 'Bass Music': 'Electronic/Dance', 'Bassline': 'Electronic/Dance',
    'Big Beat': 'Electronic/Dance', 'Bounce': 'Electronic/Dance', 'Breaks': 'Electronic/Dance',
    'Cheesy Dance': 'Electronic/Dance', 'Club Classics': 'Electronic/Dance', 'Deep House': 'Electronic/Dance',
    'Disco House': 'Electronic/Dance', 'Drum and Bass': 'Electronic/Dance', 'Dubstep': 'Electronic/Dance',
    'EDM': 'Electronic/Dance', 'Electro': 'Electronic/Dance', 'Electro House': 'Electronic/Dance',
    'Electro Swing': 'Electronic/Dance', 'Experimental': 'Electronic/Dance', 'Funky House': 'Electronic/Dance',
    'Hard Dance': 'Electronic/Dance', 'Hard House': 'Electronic/Dance', 'Hard Trance': 'Electronic/Dance',
    'Hardcore/Hardstyle': 'Electronic/Dance', 'Jungle': 'Electronic/Dance', 'Minimal': 'Electronic/Dance',
    'Minimal Techno': 'Electronic/Dance', 'Nu Disco': 'Electronic/Dance', 'Nu Rave': 'Electronic/Dance',
    'Old Skool': 'Electronic/Dance', 'Prog House': 'Electronic/Dance', 'Psy/GoaTrance': 'Electronic/Dance',
    'Retro House': 'Electronic/Dance', 'Soulful House': 'Electronic/Dance', 'Tech House': 'Electronic/Dance',
    'Trance': 'Electronic/Dance', 'Tribal House': 'Electronic/Dance', 'UK Garage': 'Electronic/Dance',

    'Alternative Folk': 'Folk/Country', 'Americana': 'Folk/Country', 'Celtic Folk': 'Folk/Country',
    'Celtic/ British Isles': 'Folk/Country', 'Classic Country': 'Folk/Country', 'Contemporary Country': 'Folk/Country',
    'Country': 'Folk/Country', 'Country Pop': 'Folk/Country', 'Folk': 'Folk/Country',
    'Indie Folk': 'Folk/Country', 'Scottish Folk': 'Folk/Country', 'Singer-Songwriter': 'Folk/Country',
    'Traditional Scottish Folk': 'Folk/Country', 'Acoustic': 'Folk/Country', 'Country/Americana': 'Folk/Country',

    'Acoustic Blues': 'Jazz/Blues/Soul', 'Big Band': 'Jazz/Blues/Soul', 'Blues': 'Jazz/Blues/Soul',
    'Cuban Jazz': 'Jazz/Blues/Soul', 'Free Jazz': 'Jazz/Blues/Soul', 'Funk': 'Jazz/Blues/Soul',
    'Fusion': 'Jazz/Blues/Soul', 'Gospel': 'Jazz/Blues/Soul', 'Jazz': 'Jazz/Blues/Soul',
    'Jazz Blues': 'Jazz/Blues/Soul', 'Jazz Funk': 'Jazz/Blues/Soul', 'Motown': 'Jazz/Blues/Soul',
    'Neo-Soul': 'Jazz/Blues/Soul', 'Northern Soul': 'Jazz/Blues/Soul', 'Psychedelic Soul': 'Jazz/Blues/Soul',
    'Soul': 'Jazz/Blues/Soul', 'Soul Jazz': 'Jazz/Blues/Soul', 'Swing': 'Jazz/Blues/Soul',

    'Death Metal/Black Metal': 'Metal/Punk', 'Goth': 'Metal/Punk', 'Goth Metal': 'Metal/Punk',
    'Hair Metal': 'Metal/Punk', 'Heavy Metal': 'Metal/Punk', 'Metal': 'Metal/Punk', 'Metalcore': 'Metal/Punk',
    'Nu-Metal': 'Metal/Punk', 'Nu Metal': 'Metal/Punk', 'Post-Punk': 'Metal/Punk', 'Power Metal': 'Metal/Punk',
    'Punk': 'Metal/Punk', 'Thrash & Speed': 'Metal/Punk', 'Death Rock': 'Metal/Punk', 'Emo': 'Metal/Punk',
    'Pop Punk': 'Metal/Punk',

    'Classical': 'Classical/Orchestral', 'Classical/Vocal': 'Classical/Orchestral',
    'Choral': 'Classical/Orchestral', 'Orchestral': 'Classical/Orchestral',

    'African': 'World/Latin/Reggae', 'Afro-Beat': 'World/Latin/Reggae', 'Afrobeat': 'World/Latin/Reggae',
    'Bollywood': 'World/Latin/Reggae', 'Cuban': 'World/Latin/Reggae', 'Latin': 'World/Latin/Reggae',
    'Pakistan': 'World/Latin/Reggae', 'Political Reggae': 'World/Latin/Reggae', 'Reggae': 'World/Latin/Reggae',
    'Rock Steady': 'World/Latin/Reggae', 'Roots Reggae': 'World/Latin/Reggae', 'Uganda': 'World/Latin/Reggae',
    'World': 'World/Latin/Reggae', 'World Dance': 'World/Latin/Reggae', 'World Music': 'World/Latin/Reggae',
    'Dancehall': 'World/Latin/Reggae', 'Dub': 'World/Latin/Reggae', 'Salsa': 'World/Latin/Reggae',
    'Ska': 'World/Latin/Reggae',

    '1960s': 'Retro/Decades', '1970s': 'Retro/Decades', '1980s': 'Retro/Decades', '1990s': 'Retro/Decades',
    '2000s': 'Retro/Decades', '2010s': 'Retro/Decades', 'Retro and Throwbacks': 'Retro/Decades',

    'Casino/Gaming': 'Non-Music/Other', "Children's Music": 'Non-Music/Other',
    "Children's Theatre": 'Non-Music/Other', 'Comedy': 'Non-Music/Other', 'Community/Civic': 'Non-Music/Other',
    'Drama': 'Non-Music/Other', 'Family': 'Non-Music/Other', 'Food & Drink': 'Non-Music/Other',
    'Miscellaneous Theatre': 'Non-Music/Other', 'Performance Art': 'Non-Music/Other',
    'Religious': 'Non-Music/Other', 'Rugby': 'Non-Music/Other', 'Rugby Union': 'Non-Music/Other',
    'Theatre': 'Non-Music/Other', 'Variety': 'Non-Music/Other', 'Burlesque': 'Non-Music/Other',
    'Spoken Word': 'Non-Music/Other', 'LGBTQ+': 'Non-Music/Other',

    'Undefined': 'Unclassified', 'Other': 'Unclassified', 'Miscellaneous': 'Unclassified',
    'Foreign': 'Unclassified', 'Covers Band/Tribute Act': 'Unclassified', 'Themed': 'Unclassified',
}


def map_to_bucket(genre_name):
    return GENRE_BUCKET_MAP.get(genre_name, 'Other/Unmapped')


# =================================================================
# TICKETMASTER
# =================================================================
def generate_month_chunks(year, months):
    chunks = []
    for month in months:
        start = pd.Timestamp(year=year, month=month, day=1)
        end = (start + pd.offsets.MonthEnd(1)).replace(hour=23, minute=59, second=59)
        chunks.append((
            start.strftime("%Y-%m-%dT%H:%M:%SZ"),
            end.strftime("%Y-%m-%dT%H:%M:%SZ")
        ))
    return chunks


def tm_fetch_page(page_number, start_date, end_date):
    params = {
        "apikey": TM_API_KEY,
        "countryCode": "GB",
        "classificationName": "Music",
        "startDateTime": start_date,
        "endDateTime": end_date,
        "sort": "date,asc",
        "size": 200,
        "page": page_number
    }
    response = requests.get(TM_BASE_URL, params=params)
    if response.status_code == 429:
        print("Rate limited — waiting 5s...")
        time.sleep(5)
        return tm_fetch_page(page_number, start_date, end_date)
    response.raise_for_status()
    return response.json()


def tm_fetch_all_pages(start_date, end_date):
    all_pages = []
    first_page = tm_fetch_page(0, start_date, end_date)
    all_pages.append(first_page)
    total_pages = first_page.get("page", {}).get("totalPages", 1)
    total_elements = first_page.get("page", {}).get("totalElements", 0)
    print(f"  TM {start_date[:7]}: {total_elements} events across {total_pages} pages")
    for page_num in range(1, total_pages):
        time.sleep(0.25)
        all_pages.append(tm_fetch_page(page_num, start_date, end_date))
    return all_pages


def tm_extract_classification(classifications_list):
    if not isinstance(classifications_list, list) or not classifications_list:
        return pd.Series({'genre': None, 'subGenre': None})
    c = classifications_list[0]
    return pd.Series({
        'genre': c.get('genre', {}).get('name'),
        'subGenre': c.get('subGenre', {}).get('name'),
    })


def tm_extract_venue(venues_list):
    if not isinstance(venues_list, list) or not venues_list:
        return pd.Series({'venue_city': None})
    v = venues_list[0]
    return pd.Series({'venue_city': v.get('city', {}).get('name')})


def pull_ticketmaster():
    date_chunks = generate_month_chunks(2026, months=[6, 7, 8])

    all_events, all_pages_flat = [], []
    for start_date, end_date in date_chunks:
        pages = tm_fetch_all_pages(start_date, end_date)
        all_pages_flat.extend(pages)
        for page in pages:
            all_events.extend(page.get("_embedded", {}).get("events", []))
        time.sleep(0.5)

    # dedup on event id
    seen_ids, deduped = set(), []
    for event in all_events:
        eid = event.get('id')
        if eid not in seen_ids:
            seen_ids.add(eid)
            deduped.append(event)
    all_events = deduped
    print(f"Ticketmaster total after dedup: {len(all_events)}")

    for i, page in enumerate(all_pages_flat):
        with open(RAW_DIR / f"tm_page{i}.json", "w") as f:
            json.dump(page, f)

    df_raw = pd.json_normalize(all_events)
    classification_cols = df_raw['classifications'].apply(tm_extract_classification)
    venue_cols = df_raw['_embedded.venues'].apply(tm_extract_venue)
    df = pd.concat([df_raw, classification_cols, venue_cols], axis=1)

    df_tm = df[['id', 'name', 'dates.start.localDate', 'genre', 'venue_city']].copy()
    df_tm = df_tm.rename(columns={'dates.start.localDate': 'date', 'venue_city': 'city_name'})
    df_tm['city_clean'] = df_tm['city_name'].str.split(',').str[0].str.strip().str.title()
    df_tm['genres_bucketed'] = df_tm['genre'].apply(lambda g: [map_to_bucket(g)])

    return df_tm[['id', 'name', 'date', 'city_clean', 'genres_bucketed']].rename(columns={'city_clean': 'city'})


# =================================================================
# SKIDDLE
# =================================================================
def sk_fetch_page(offset):
    response = requests.get(
        SK_BASE_URL,
        params={
            "api_key": SK_API_KEY,
            "country": "GB",
            "eventcode": "FEST",
            "description": 1,
            "minDate": "2026-06-01",
            "maxDate": "2026-08-31",
            "limit": 100,
            "offset": offset
        }
    )
    response.raise_for_status()
    return response.json()


def pull_skiddle():
    first_page = sk_fetch_page(0)
    total = int(first_page.get('totalcount', 0))
    print(f"Skiddle total: {total}")

    all_events = list(first_page['results'])
    offset = 100
    while offset < total:
        time.sleep(0.25)
        page = sk_fetch_page(offset)
        all_events.extend(page['results'])
        offset += 100

    with open(RAW_DIR / "skiddle_raw.json", "w") as f:
        json.dump(all_events, f)

    df_sk = pd.json_normalize(all_events)

    non_uk_towns = ['Paris']
    df_sk = df_sk[~df_sk['venue.town'].isin(non_uk_towns)].copy()
    df_sk['city_clean'] = df_sk['venue.town'].str.strip().str.title()

    def extract_genre_names(genres_list):
        if not isinstance(genres_list, list):
            return []
        return [g.get('name') for g in genres_list if isinstance(g, dict) and g.get('name')]

    df_sk['genre_names'] = df_sk['genres'].apply(extract_genre_names)
    df_sk['genres_bucketed'] = df_sk['genre_names'].apply(lambda gs: list({map_to_bucket(g) for g in gs}))

    df_sk_final = df_sk[['id', 'eventname', 'startdate', 'city_clean', 'genres_bucketed']].copy()
    df_sk_final = df_sk_final.rename(columns={'eventname': 'name', 'startdate': 'date', 'city_clean': 'city'})
    return df_sk_final


# =================================================================
# COMBINE
# =================================================================
def main():
    print(f"Starting pull at {datetime.now()}")

    df_tm = pull_ticketmaster()
    df_tm['date'] = pd.to_datetime(df_tm['date'], utc=True).dt.tz_localize(None).dt.normalize()
    df_tm['name_clean'] = df_tm['name'].str.lower().str.strip()

    df_sk = pull_skiddle()
    df_sk['date'] = pd.to_datetime(df_sk['date'], utc=True).dt.tz_localize(None).dt.normalize()
    df_sk['name_clean'] = df_sk['name'].str.lower().str.strip()

    # remove exact-match duplicates (name + date), keep Skiddle version
    exact_matches = df_tm.merge(df_sk, on=['name_clean', 'date'], suffixes=('_tm', '_sk'))
    tm_ids_to_drop = exact_matches['id_tm']
    df_tm = df_tm[~df_tm['id'].isin(tm_ids_to_drop)]
    print(f"Removed {len(exact_matches)} exact-match duplicates from Ticketmaster")

    df_tm['source'] = 'ticketmaster'
    df_sk['source'] = 'skiddle'

    df_combined = pd.concat([
        df_tm[['id', 'name', 'date', 'city', 'genres_bucketed', 'source']],
        df_sk[['id', 'name', 'date', 'city', 'genres_bucketed', 'source']]
    ], ignore_index=True)

    df_combined = df_combined.dropna(subset=['city'])

    df_combined.to_csv("df_combined_genre.csv", index=False)
    print(f"Wrote {len(df_combined)} rows to df_combined_genre.csv")

    with open("last_updated.txt", "w") as f:
        f.write(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    print(f"Finished at {datetime.now()}")


if __name__ == "__main__":
    main()