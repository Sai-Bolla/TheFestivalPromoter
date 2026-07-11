import pandas as pd
import numpy as np
from typing import List, Tuple, Optional
import re
from fuzzywuzzy import fuzz, process


class AdvancedDataCleaner:
    """Advanced data cleaning with fuzzy matching and validation"""
    
    def __init__(self):
        pass
    
    def clean_venue_names(self, df: pd.DataFrame, threshold: int = 85) -> pd.DataFrame:
        """Clean and standardize venue names using fuzzy matching"""
        if df.empty:
            return df
        
        df_clean = df.copy()
        
        # Get unique venue names
        venues = df_clean['venue_name'].unique()
        
        # Group similar venue names
        venue_groups = {}
        processed = set()
        
        for venue in venues:
            if venue in processed:
                continue
            
            # Find similar venues
            similar = [venue]
            for other in venues:
                if other in processed or other == venue:
                    continue
                if fuzz.ratio(str(venue).lower(), str(other).lower()) > threshold:
                    similar.append(other)
                    processed.add(other)
            
            processed.add(venue)
            
            if len(similar) > 1:
                # Get the most frequently occurring name
                name_counts = df_clean[df_clean['venue_name'].isin(similar)]['venue_name'].value_counts()
                standard_name = name_counts.index[0]
                
                for s in similar:
                    venue_groups[s] = standard_name
            else:
                venue_groups[venue] = venue
        
        # Apply standardization
        df_clean['venue_name_cleaned'] = df_clean['venue_name'].map(venue_groups).fillna(df_clean['venue_name'])
        
        print(f"🏷️ Standardized {len(venue_groups)} venue names (threshold={threshold}%)")
        return df_clean
    
    def extract_event_categories(self, df: pd.DataFrame) -> pd.DataFrame:
        """Extract and standardize event categories from genre data"""
        if df.empty:
            return df
        
        df_clean = df.copy()
        
        # Expanded genre mapping
        genre_mapping = {
            'rock': 'Rock',
            'pop': 'Pop',
            'electronic': 'Electronic',
            'hip hop': 'Hip Hop',
            'rap': 'Hip Hop',
            'jazz': 'Jazz',
            'classical': 'Classical',
            'folk': 'Folk',
            'metal': 'Metal',
            'reggae': 'Reggae',
            'blues': 'Blues',
            'country': 'Country',
            'indie': 'Indie',
            'alternative': 'Alternative',
            'punk': 'Punk',
            'soul': 'Soul',
            'r&b': 'R&B',
            'dance': 'Dance',
            'house': 'Electronic',
            'techno': 'Electronic',
            'drum and bass': 'Electronic',
            'ambient': 'Electronic',
            'experimental': 'Experimental',
            'world': 'World Music',
            'latin': 'Latin',
            'opera': 'Classical',
            'musical': 'Musical/Theatre'
        }
        
        def categorise_genre(genre_str):
            if pd.isna(genre_str) or genre_str == 'N/A' or genre_str == '':
                return 'Uncategorised'
            
            genre_lower = str(genre_str).lower()
            
            # Check for exact matches first
            for key, value in genre_mapping.items():
                if key == genre_lower:
                    return value
            
            # Check for partial matches
            for key, value in genre_mapping.items():
                if key in genre_lower:
                    return value
                
            # Check multiple genres (comma-separated)
            genres = [g.strip().lower() for g in genre_str.split(',')]
            
            # Try to categorize each genre
            for g in genres:
                for key, value in genre_mapping.items():
                    if key in g:
                        return value
            
            # If no match, return the first genre or 'Uncategorised'
            return genres[0].title() if genres else 'Uncategorised'
        
        df_clean['event_category'] = df_clean['genre'].apply(categorise_genre)
        print(f"📂 Categorized {len(df_clean)} events into {df_clean['event_category'].nunique()} categories")
        return df_clean
    
    def add_event_quality_score(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add a quality score (0-10) based on data completeness"""
        if df.empty:
            return df
        
        df_clean = df.copy()
        
        # Vectorized approach - MUCH faster than iterrows()
        scores = pd.Series(0, index=df_clean.index)
        
        # Has name (2 points)
        scores += np.where(
            (df_clean['event_name'].notna()) & (df_clean['event_name'] != 'Unknown Event'),
            2, 0
        )
        
        # Valid coordinates (3 points)
        scores += np.where(
            (df_clean['latitude'] != 0) & (df_clean['longitude'] != 0) &
            (df_clean['latitude'].notna()) & (df_clean['longitude'].notna()),
            3, 0
        )
        
        # Has date (2 points)
        scores += np.where(
            (df_clean['date'].notna()) & (df_clean['date'] != 'Date TBC'),
            2, 0
        )
        
        # Has genre (1 point)
        scores += np.where(
            (df_clean['genre'].notna()) & (df_clean['genre'] != 'N/A'),
            1, 0
        )
        
        # Has price (1 point)
        scores += np.where(
            (df_clean['price'].notna()) & (df_clean['price'] != 'TBC'),
            1, 0
        )
        
        # Has URL (1 point)
        scores += np.where(
            (df_clean['url'].notna()) & (df_clean['url'] != '#'),
            1, 0
        )
        
        df_clean['quality_score'] = scores
        
        # Add quality rating
        def get_rating(score):
            if score >= 8:
                return 'Excellent'
            elif score >= 6:
                return 'Good'
            elif score >= 4:
                return 'Fair'
            else:
                return 'Poor'
        
        df_clean['quality_rating'] = df_clean['quality_score'].apply(get_rating)
        
        print(f"⭐ Added quality scores (avg: {df_clean['quality_score'].mean():.1f}/10)")
        return df_clean
    
    def validate_event_data(self, df: pd.DataFrame, min_quality: int = 5) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Validate data and return valid/invalid DataFrames with reasons"""
        if df.empty:
            return df, df
        
        df_clean = df.copy()
        
        # Track validation failures
        validation_reasons = []
        
        # Check each row
        for idx, row in df_clean.iterrows():
            reasons = []
            
            # Check event name
            if pd.isna(row['event_name']) or row['event_name'] == 'Unknown Event':
                reasons.append('Missing or invalid event name')
            
            # Check venue name
            if pd.isna(row['venue_name']) or row['venue_name'] == 'Unknown Venue':
                reasons.append('Missing venue name')
            
            # Check coordinates
            if not (49.9 <= row['latitude'] <= 60.8):
                reasons.append(f'Latitude out of UK range: {row["latitude"]}')
            if not (-10.5 <= row['longitude'] <= 1.8):
                reasons.append(f'Longitude out of UK range: {row["longitude"]}')
            
            # Check quality score
            if row.get('quality_score', 0) < min_quality:
                reasons.append(f'Low quality score: {row.get("quality_score", 0)}/10')
            
            # Check date
            if pd.isna(row['date']) or row['date'] == 'Date TBC':
                reasons.append('Missing date')
            
            validation_reasons.append('; '.join(reasons) if reasons else 'Valid')
        
        df_clean['validation_reason'] = validation_reasons
        
        # Split into valid and invalid
        is_valid = df_clean['validation_reason'] == 'Valid'
        valid_df = df_clean[is_valid].copy()
        invalid_df = df_clean[~is_valid].copy()
        
        print(f"✅ Valid events: {len(valid_df)}")
        print(f"⚠️ Invalid events: {len(invalid_df)}")
        
        # Print summary of invalid reasons
        if not invalid_df.empty:
            reason_counts = invalid_df['validation_reason'].value_counts().head(5)
            print("Top invalid reasons:")
            for reason, count in reason_counts.items():
                print(f"  - {reason}: {count}")
        
        return valid_df, invalid_df
    
    def deduplicate_with_confidence(self, df: pd.DataFrame, threshold: int = 90) -> pd.DataFrame:
        """Advanced deduplication with confidence scoring"""
        if len(df) < 2:
            return df
        
        # Reset index to ensure we have clean integer indices
        df_clean = df.reset_index(drop=True).copy()
        duplicates = set()
        
        # Sort by quality score first (higher quality = keep)
        df_clean = df_clean.sort_values('quality_score', ascending=False).reset_index(drop=True)
        
        # Compare events
        for i in range(len(df_clean)):
            if i in duplicates:
                continue
            
            row_i = df_clean.iloc[i]
            
            for j in range(i + 1, len(df_clean)):
                if j in duplicates:
                    continue
                
                row_j = df_clean.iloc[j]
                
                # Calculate similarity scores
                name_sim = fuzz.ratio(str(row_i['event_name']).lower(), str(row_j['event_name']).lower())
                venue_sim = fuzz.ratio(str(row_i['venue_name']).lower(), str(row_j['venue_name']).lower())
                
                # Check if dates are close (within 7 days)
                date_sim = 0
                try:
                    date_i = pd.to_datetime(row_i['date'], errors='coerce')
                    date_j = pd.to_datetime(row_j['date'], errors='coerce')
                    if pd.notna(date_i) and pd.notna(date_j):
                        days_diff = abs((date_i - date_j).days)
                        if days_diff <= 7:
                            date_sim = max(0, 100 - (days_diff * 10))  # Convert to similarity score
                except:
                    pass
                
                # Combined similarity score (weighted)
                combined_score = (name_sim * 0.5) + (venue_sim * 0.3) + (date_sim * 0.2)
                
                # If similar enough, mark as duplicate
                if combined_score > threshold:
                    # Keep the one with higher quality score
                    if row_i['quality_score'] >= row_j['quality_score']:
                        duplicates.add(j)
                    else:
                        duplicates.add(i)
                        break
        
        # Remove duplicates - FIXED: drop by position using iloc
        if duplicates:
            # Convert to list and sort in reverse order to avoid index shifting
            duplicate_indices = sorted(list(duplicates), reverse=True)
            for idx in duplicate_indices:
                df_clean = df_clean.drop(index=idx)
        
        # Reset index after dropping duplicates
        df_clean = df_clean.reset_index(drop=True)
        
        print(f"🔍 Removed {len(duplicates)} duplicate events (threshold={threshold}%)")
        return df_clean
    
    def analyze_data_quality(self, df: pd.DataFrame) -> dict:
        """Generate a comprehensive quality report"""
        if df.empty:
            return {}
        
        report = {
            'total_events': len(df),
            'unique_venues': df['venue_name'].nunique(),
            'unique_sources': df['source'].nunique() if 'source' in df else 0,
            'quality_stats': {
                'mean': df['quality_score'].mean() if 'quality_score' in df else 0,
                'median': df['quality_score'].median() if 'quality_score' in df else 0,
                'min': df['quality_score'].min() if 'quality_score' in df else 0,
                'max': df['quality_score'].max() if 'quality_score' in df else 0,
            },
            'quality_distribution': df['quality_rating'].value_counts().to_dict() if 'quality_rating' in df else {},
            'missing_data': {
                'missing_names': df['event_name'].isna().sum(),
                'missing_venues': df['venue_name'].isna().sum(),
                'missing_dates': df['date'].isna().sum(),
                'missing_coords': ((df['latitude'] == 0) | (df['longitude'] == 0)).sum(),
            },
            'category_distribution': df['event_category'].value_counts().head(10).to_dict() if 'event_category' in df else {},
            'source_distribution': df['source'].value_counts().to_dict() if 'source' in df else {},
        }
        
        return report
    
    def print_quality_report(self, df: pd.DataFrame):
        """Print a formatted quality report"""
        report = self.analyze_data_quality(df)
        
        print("\n" + "="*50)
        print("📊 DATA QUALITY REPORT")
        print("="*50)
        
        print("📈 Overview:")
        print(f"  Total Events: {report['total_events']}")
        print(f"  Unique Venues: {report['unique_venues']}")
        
        print("⭐ Quality Scores:")
        for stat, value in report['quality_stats'].items():
            print(f"  {stat.capitalize()}: {value:.1f}")
        
        print("📊 Quality Ratings:")
        for rating, count in report['quality_distribution'].items():
            print(f"  {rating}: {count} ({count/report['total_events']*100:.1f}%)")
        
        print("⚠️ Missing Data:")
        for field, count in report['missing_data'].items():
            if count > 0:
                print(f"  {field}: {count} ({count/report['total_events']*100:.1f}%)")
        
        print("📂 Top Categories:")
        for category, count in list(report['category_distribution'].items())[:5]:
            print(f"  {category}: {count}")
        
        print("="*50)


if __name__ == "__main__":
    # Load data
    try:
        df = pd.read_csv("data/processed/events_cleaned_latest.csv")
        print(f"📂 Loaded {len(df)} events")
        
        # Initialise cleaner
        cleaner = AdvancedDataCleaner()
        
        # Cleaning
        print("\n🔧 Starting data cleaning...")
        
        # 1. Clean venue names
        print("\n1️⃣ Standardizing venue names...")
        df = cleaner.clean_venue_names(df)
        
        # 2. Extract categories
        print("\n2️⃣ Extracting event categories...")
        df = cleaner.extract_event_categories(df)
        
        # 3. Add quality scores
        print("\n3️⃣ Adding quality scores...")
        df = cleaner.add_event_quality_score(df)
        
        # 4. Deduplicate
        print("\n4️⃣ Deduplicating events...")
        df = cleaner.deduplicate_with_confidence(df)
        
        # 5. Validate
        print("\n5️⃣ Validating data...")
        valid, invalid = cleaner.validate_event_data(df)
        
        # 6. Generate quality report
        print("\n6️⃣ Generating quality report...")
        cleaner.print_quality_report(valid)
        
        # Save results
        valid.to_csv("data/processed/events_valid.csv", index=False)
        invalid.to_csv("data/processed/events_invalid.csv", index=False)
        
        print(f"\n✅ Saved {len(valid)} valid events to data/processed/events_valid.csv")
        print(f"⚠️ Saved {len(invalid)} invalid events to data/processed/events_invalid.csv")
        
    except FileNotFoundError:
        print("❌ Error: events_cleaned_latest.csv not found. Please run data_pipeline.py first.")
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()