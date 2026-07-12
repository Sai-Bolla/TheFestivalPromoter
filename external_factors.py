import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import requests
from typing import Dict, List, Optional, Tuple
import holidays
from dataclasses import dataclass
import json


@dataclass
class ExternalFactor:
    """Represents an external factor that might affect events"""
    name: str
    category: str
    date_range: Tuple[datetime, datetime]
    impact: str  # 'positive', 'negative', 'neutral'
    description: str
    source: str


class ExternalFactorsAnalyzer:
    """Analyse external factors affecting event schedules"""
    
    def __init__(self):
        # UK holidays
        self.uk_holidays = holidays.UnitedKingdom(subdiv='England')
        
        # Major UK events (expand this)
        self.major_events = {
            'Glastonbury': {'month': 6, 'week': 4, 'days': 5},
            'Reading Festival': {'month': 8, 'week': 3, 'days': 3},
            'Leeds Festival': {'month': 8, 'week': 3, 'days': 3},
            'BBC Proms': {'month': 7, 'week': 1, 'days': 56},
            'Edinburgh Fringe': {'month': 8, 'week': 1, 'days': 25},
            'Notting Hill Carnival': {'month': 8, 'week': 4, 'days': 2},
            'Wireless Festival': {'month': 7, 'week': 2, 'days': 3},
            'British Summer Time': {'month': 6, 'week': 2, 'days': 10},
        }
        
        # Seasonal patterns
        self.seasonal_factors = {
            'Summer Holidays': {'months': [7, 8], 'impact': 'positive'},
            'Christmas Season': {'months': [12], 'impact': 'positive'},
            'January Lull': {'months': [1], 'impact': 'negative'},
            'Exam Season': {'months': [5, 6], 'impact': 'negative'},
            'Bank Holidays': {'impact': 'mixed'},
        }
    
    def get_holidays_in_range(self, start_date: datetime, end_date: datetime) -> List[Dict]:
        """Get UK holidays within date range"""
        holidays_in_range = []
        
        current = start_date
        while current <= end_date:
            if current in self.uk_holidays:
                holidays_in_range.append({
                    'date': current,
                    'name': self.uk_holidays[current],
                    'day_of_week': current.strftime('%A')
                })
            current += timedelta(days=1)
        
        return holidays_in_range
    
    def check_major_events(self, year: int, month: int) -> List[Dict]:
        """Check if major events are happening in a given month"""
        events = []
        
        for event_name, event_info in self.major_events.items():
            if event_info['month'] == month:
                # Estimate event start date
                start_date = datetime(year, month, 1)
                # Approximate week calculation
                week_offset = (event_info['week'] - 1) * 7
                event_start = start_date + timedelta(days=week_offset)
                event_end = event_start + timedelta(days=event_info['days'])
                
                events.append({
                    'name': event_name,
                    'start_date': event_start,
                    'end_date': event_end,
                    'duration': event_info['days'],
                    'category': 'Music Festival'
                })
        
        return events
    
    def analyze_seasonal_patterns(self, gap_month: int) -> Dict:
        """Analyze seasonal factors for a given month"""
        patterns = []
        
        for season, info in self.seasonal_factors.items():
            if 'months' in info and gap_month in info['months']:
                patterns.append({
                    'factor': season,
                    'impact': info['impact'],
                    'description': f"{season} typically has {info['impact']} impact on events"
                })
        
        return {'patterns': patterns}
    
    def get_weather_impact(self, month: int) -> Dict:
        """Analyze weather impact (simplified)"""
        weather_impacts = {
            1: {'condition': 'Cold/Wet', 'impact': 'negative', 'description': 'January weather often reduces outdoor event attendance'},
            2: {'condition': 'Cold/Wet', 'impact': 'negative', 'description': 'February weather is typically cold'},
            3: {'condition': 'Cool', 'impact': 'neutral', 'description': 'March weather improving but unpredictable'},
            4: {'condition': 'Mild', 'impact': 'positive', 'description': 'Spring weather encourages outdoor events'},
            5: {'condition': 'Mild/Warm', 'impact': 'positive', 'description': 'May weather ideal for events'},
            6: {'condition': 'Warm', 'impact': 'positive', 'description': 'June weather supports outdoor events'},
            7: {'condition': 'Warm', 'impact': 'positive', 'description': 'July is peak event season'},
            8: {'condition': 'Warm', 'impact': 'positive', 'description': 'August continues strong event season'},
            9: {'condition': 'Mild', 'impact': 'neutral', 'description': 'September weather still good'},
            10: {'condition': 'Cool', 'impact': 'neutral', 'description': 'October cooling down'},
            11: {'condition': 'Cold/Wet', 'impact': 'negative', 'description': 'November weather often poor'},
            12: {'condition': 'Cold', 'impact': 'mixed', 'description': 'December weather cold but holiday season boosts events'},
        }
        
        return weather_impacts.get(month, {'condition': 'Unknown', 'impact': 'neutral', 'description': 'Weather impact unknown'})
    
    def analyze_gap_causes(self, df: pd.DataFrame, gap_start: datetime, gap_end: datetime) -> Dict:
        """Comprehensive analysis of why a gap might exist"""
        
        gap_analysis = {
            'gap_dates': {
                'start': gap_start,
                'end': gap_end,
                'duration_days': (gap_end - gap_start).days,
                'month': gap_start.strftime('%B'),
                'year': gap_start.year,
                'day_of_week': gap_start.strftime('%A')
            },
            'external_factors': [],
            'opportunities': [],
            'recommendations': []
        }
        
        # 1. Check holidays during gap
        holidays_in_gap = self.get_holidays_in_range(gap_start, gap_end)
        if holidays_in_gap:
            gap_analysis['external_factors'].append({
                'type': 'Holiday',
                'details': holidays_in_gap,
                'impact': 'mixed',
                'description': 'Bank/Public holidays during this period'
            })
        
        # 2. Check major events nearby
        month = gap_start.month
        year = gap_start.year
        major_events = self.check_major_events(year, month)
        if major_events:
            gap_analysis['external_factors'].append({
                'type': 'Major Events',
                'details': major_events,
                'impact': 'negative',
                'description': 'Major events may be drawing audiences away'
            })
        
        # 3. Seasonal patterns
        seasonal = self.analyze_seasonal_patterns(month)
        if seasonal['patterns']:
            gap_analysis['external_factors'].append({
                'type': 'Seasonal',
                'details': seasonal['patterns'],
                'impact': 'mixed',
                'description': f"Seasonal factors: {', '.join([p['factor'] for p in seasonal['patterns']])}"
            })
        
        # 4. Weather impact
        weather = self.get_weather_impact(month)
        gap_analysis['external_factors'].append({
            'type': 'Weather',
            'details': weather,
            'impact': weather['impact'],
            'description': weather['description']
        })
        
        # 5. Economic factors (simplified)
        # In reality, you'd use economic data APIs
        gap_analysis['external_factors'].append({
            'type': 'Economic',
            'details': {
                'note': 'Consider checking local economic conditions',
                'data_source': 'ONS or local business surveys'
            },
            'impact': 'neutral',
            'description': 'Economic factors may influence event scheduling'
        })
        
        return gap_analysis
    
    def identify_opportunities(self, gap: Dict, events_df: pd.DataFrame) -> List[Dict]:
        """Identify opportunities to fill event gaps"""
        
        opportunities = []
        gap_start = gap['gap_dates']['start']
        gap_end = gap['gap_dates']['end']
        month = gap_start.month
        
        # 1. Check if gap is during a holiday period
        holidays = self.get_holidays_in_range(gap_start, gap_end)
        if holidays:
            opportunities.append({
                'type': 'Holiday Event',
                'description': f"Create special events during holidays: {', '.join([h['name'] for h in holidays])}",
                'target_audience': 'Families, tourists, locals',
                'potential_venues': 'Indoor venues, community centers, pubs',
                'suggestion': 'Family-friendly events, special holiday entertainment'
            })
        
        # 2. Check if weather is favorable
        weather = self.get_weather_impact(month)
        if weather['impact'] == 'positive' or weather['impact'] == 'neutral':
            opportunities.append({
                'type': 'Weather-Favorable Event',
                'description': f"Good weather conditions ({weather['condition']}) - opportunity for outdoor events",
                'target_audience': 'General public, young adults',
                'potential_venues': 'Parks, outdoor spaces, beer gardens',
                'suggestion': 'Outdoor concerts, pop-up events, food and music festivals'
            })
        
        # 3. Check if there's a demand pattern
        # Look at event frequency around this time in previous years (if data available)
        if 'date_parsed' in events_df.columns:
            events_df['year'] = events_df['date_parsed'].dt.year
            events_df['month'] = events_df['date_parsed'].dt.month
            
            # Check if this month typically has low events
            historical_count = len(events_df[events_df['month'] == month])
            avg_count = len(events_df) / 12  # Average per month
            
            if historical_count < avg_count * 0.7:  # 30% below average
                opportunities.append({
                    'type': 'Underserved Period',
                    'description': f"Historically low event count ({historical_count} vs {avg_count:.0f} avg) - opportunity to establish new events",
                    'target_audience': 'Event promoters, local businesses',
                    'potential_venues': 'Various venues',
                    'suggestion': 'Create a recurring event series to establish a presence in this period'
                })
        
        # 4. Competition analysis
        major_events = self.check_major_events(gap_start.year, month)
        if major_events:
            opportunities.append({
                'type': 'Counter-Programming',
                'description': f"Major events ({', '.join([e['name'] for e in major_events])}) nearby - create alternative events",
                'target_audience': 'Those seeking alternative entertainment',
                'potential_venues': 'Smaller venues, specialist spaces',
                'suggestion': 'Smaller, niche events that contrast with mainstream festivals'
            })
        
        # 5. Specific recommendations based on gap duration
        duration = gap['gap_dates']['duration_days']
        if duration >= 7:  # Week-long gap
            opportunities.append({
                'type': 'Extended Gap Opportunity',
                'description': "7+ day gap - opportunity for a mini-festival or series",
                'target_audience': 'Event organizers, community groups',
                'potential_venues': 'Multiple venues',
                'suggestion': 'Organize a "Fill the Gap" mini-festival or weekly event series'
            })
        elif duration >= 3:  # Short gap
            opportunities.append({
                'type': 'Short Gap Opportunity',
                'description': f"{duration}-day gap - opportunity for special events",
                'target_audience': 'Local venues, promoters',
                'potential_venues': 'Existing venues',
                'suggestion': 'Last-minute event bookings, special promotions'
            })
        
        return opportunities


class OpportunityFinder:
    """Find and prioritize opportunities"""
    
    def __init__(self):
        self.priority_weights = {
            'Holiday Event': 5,
            'Weather-Favorable Event': 4,
            'Underserved Period': 5,
            'Counter-Programming': 3,
            'Extended Gap Opportunity': 4,
            'Short Gap Opportunity': 2,
            'Targeted Marketing': 3,
            'Venue Partnership': 4
        }
    
    def prioritize_opportunities(self, opportunities: List[Dict]) -> List[Dict]:
        """Prioritize opportunities based on potential impact"""
        for opp in opportunities:
            # Add priority score
            base_score = self.priority_weights.get(opp['type'], 3)
            
            # Adjust score based on factors
            if 'holiday' in opp['description'].lower():
                base_score += 1
            if 'weather' in opp['description'].lower() and 'favorable' in opp['description'].lower():
                base_score += 1
            if 'underserved' in opp['type'].lower() or 'gap' in opp['type'].lower():
                base_score += 1
            
            opp['priority_score'] = min(base_score, 10)  # Cap at 10
            opp['priority_level'] = self.get_priority_level(opp['priority_score'])
        
        # Sort by priority score
        return sorted(opportunities, key=lambda x: x['priority_score'], reverse=True)
    
    def get_priority_level(self, score: int) -> str:
        """Get priority level based on score"""
        if score >= 8:
            return 'High'
        elif score >= 5:
            return 'Medium'
        else:
            return 'Low'