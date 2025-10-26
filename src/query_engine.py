"""
Query Engine Module for Project Samarth
Handles natural language query parsing and processing
"""

import re
import time
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
import numpy as np
from datetime import datetime
import logging

from .config import Config
from .data_fetcher import DataFetcher
from .analytics import AnalyticsEngine
from .visualizer import Visualizer

logging.basicConfig(level=getattr(logging, Config.LOG_LEVEL))
logger = logging.getLogger(__name__)


class QueryEngine:
    """
    Core query processing engine with NLP capabilities
    Parses natural language queries and orchestrates data retrieval and analysis
    """
    
    def __init__(self):
        self.config = Config()
        self.data_fetcher = DataFetcher()
        self.analytics = AnalyticsEngine()
        self.visualizer = Visualizer()
        
        # Query patterns for intent classification
        self.patterns = {
            'compare': r'\b(compare|versus|vs|difference between)\b',
            'top': r'\b(top|best|highest|maximum|most)\s+(\d+)\b',
            'trend': r'\b(trend|over time|historical|growth|decline)\b',
            'correlation': r'\b(correlation|relationship|impact|effect)\b',
            'ranking': r'\b(rank|order|sort)\b',
            'average': r'\b(average|mean|avg)\b',
            'total': r'\b(total|sum|aggregate)\b',
            'production': r'\b(production|yield|output|harvest)\b',
            'rainfall': r'\b(rainfall|precipitation|monsoon)\b',
            'district': r'\b(district|region|area)\b',
            'suggest|recommend': r'\b(suggest|recommend|should|policy)\b'
        }
    
    def process_query(self, query: str) -> Dict[str, Any]:
        """
        Main query processing pipeline
        
        Args:
            query: Natural language query string
        
        Returns:
            Dict containing answer, data, visualizations, and sources
        """
        start_time = time.time()
        
        logger.info(f"Processing query: {query}")
        
        try:
            # Step 1: Parse query and extract entities
            parsed_query = self._parse_query(query)
            logger.info(f"Parsed query: {parsed_query}")
            
            # Step 2: Fetch required data
            data_results = self._fetch_data_for_query(parsed_query)
            
            # Step 3: Perform analysis
            analysis_results = self._analyze_data(parsed_query, data_results)
            
            # Step 4: Generate visualizations
            visualizations = self._generate_visualizations(parsed_query, analysis_results)
            
            # Step 5: Generate natural language answer
            answer = self._generate_answer(parsed_query, analysis_results)
            
            # Step 6: Collect source citations
            sources = self._collect_sources(data_results)
            
            processing_time = time.time() - start_time
            
            return {
                'answer': answer,
                'data': analysis_results.get('data', {}),
                'visualizations': visualizations,
                'sources': sources,
                'confidence': analysis_results.get('confidence', 0.8),
                'processing_time': processing_time,
                'data_points': analysis_results.get('data_points', 0),
                'query_type': parsed_query['intent']
            }
            
        except Exception as e:
            logger.error(f"Error processing query: {e}", exc_info=True)
            return {
                'answer': f"I encountered an error processing your query: {str(e)}. Please try rephrasing your question.",
                'data': {},
                'visualizations': [],
                'sources': [],
                'confidence': 0.0,
                'processing_time': time.time() - start_time,
                'data_points': 0,
                'error': str(e)
            }
    
    def _parse_query(self, query: str) -> Dict[str, Any]:
        """
        Parse natural language query to extract intent and entities
        
        Returns:
            Dict with intent, states, crops, years, metrics, etc.
        """
        query_lower = query.lower()
        
        # Detect intent
        intent = self._detect_intent(query_lower)
        
        # Extract entities
        states = self._extract_states(query)
        crops = self._extract_crops(query)
        years = self._extract_years(query)
        top_n = self._extract_top_n(query)
        districts = self._extract_districts(query)
        
        # Determine required metrics
        metrics = []
        if re.search(self.patterns['rainfall'], query_lower):
            metrics.append('rainfall')
        if re.search(self.patterns['production'], query_lower):
            metrics.append('production')
        
        return {
            'original_query': query,
            'intent': intent,
            'states': states,
            'crops': crops,
            'years': years,
            'top_n': top_n,
            'districts': districts,
            'metrics': metrics if metrics else ['production', 'rainfall']
        }
    
    def _detect_intent(self, query: str) -> str:
        """Detect the primary intent of the query"""
        for intent, pattern in self.patterns.items():
            if re.search(pattern, query):
                if intent in ['compare', 'top', 'trend', 'correlation']:
                    return intent
        
        # Default intent
        if any(word in query for word in ['what', 'which', 'list']):
            return 'retrieve'
        else:
            return 'compare'
    
    def _extract_states(self, query: str) -> List[str]:
        """Extract Indian state names from query"""
        found_states = []
        
        # Check full state names
        for state in self.config.INDIAN_STATES:
            if state.lower() in query.lower():
                found_states.append(state)
        
        # Check abbreviations
        for abbr, full_name in self.config.STATE_ABBREVIATIONS.items():
            if f" {abbr.lower()} " in f" {query.lower()} " or f" {abbr.lower()}," in f" {query.lower()},":
                if full_name not in found_states:
                    found_states.append(full_name)
        
        return found_states
    
    def _extract_crops(self, query: str) -> List[str]:
        """Extract crop names from query"""
        found_crops = []
        query_lower = query.lower()
        
        for crop in self.config.MAJOR_CROPS:
            if crop.lower() in query_lower:
                found_crops.append(crop)
        
        # Check for crop categories
        for category, crop_list in self.config.CROP_CATEGORIES.items():
            if category in query_lower:
                found_crops.extend(crop_list)
        
        return list(set(found_crops))  # Remove duplicates
    
    def _extract_years(self, query: str) -> List[int]:
        """Extract year ranges from query"""
        years = []
        
        # Extract explicit years (e.g., 2015, 2020)
        year_matches = re.findall(r'\b(19|20)\d{2}\b', query)
        years.extend([int(y) for y in year_matches])
        
        # Extract relative years (e.g., "last 5 years")
        last_n_match = re.search(r'last\s+(\d+)\s+years?', query.lower())
        if last_n_match:
            n = int(last_n_match.group(1))
            current_year = datetime.now().year
            years = list(range(current_year - n, current_year))
        
        # Extract decade references
        decade_match = re.search(r'over (?:the )?(?:last |past )?decade', query.lower())
        if decade_match:
            current_year = datetime.now().year
            years = list(range(current_year - 10, current_year))
        
        # Default to last 5 years if no years specified
        if not years:
            current_year = datetime.now().year
            years = list(range(current_year - 5, current_year))
        
        return sorted(set(years))
    
    def _extract_top_n(self, query: str) -> int:
        """Extract top N number from query (e.g., 'top 5')"""
        match = re.search(r'top\s+(\d+)', query.lower())
        if match:
            return int(match.group(1))
        
        # Check for other patterns
        match = re.search(r'(\d+)\s+(?:most|best|highest)', query.lower())
        if match:
            return int(match.group(1))
        
        return 5  # Default
    
    def _extract_districts(self, query: str) -> List[str]:
        """Extract district names from query"""
        districts = []
        district_pattern = r'(\w+)\s+district'
        matches = re.findall(district_pattern, query, re.IGNORECASE)
        districts.extend(matches)
        return districts
    
    def _fetch_data_for_query(self, parsed_query: Dict) -> Dict[str, Any]:
        """Fetch all required data based on parsed query"""
        data_results = {}
        
        states = parsed_query['states']
        crops = parsed_query['crops']
        years = parsed_query['years']
        metrics = parsed_query['metrics']
        
        # Fetch rainfall data if needed
        if 'rainfall' in metrics and states:
            try:
                rainfall_df = self.data_fetcher.fetch_rainfall_data(states, years)
                data_results['rainfall'] = {
                    'dataframe': rainfall_df,
                    'source': self.data_fetcher.get_source_citation('imd_rainfall', {
                        'states': states,
                        'years': years
                    })
                }
            except Exception as e:
                logger.error(f"Error fetching rainfall data: {e}")
        
        # Fetch crop production data if needed
        if 'production' in metrics and states:
            try:
                production_df = self.data_fetcher.fetch_crop_production(
                    states, crops if crops else None, years
                )
                data_results['production'] = {
                    'dataframe': production_df,
                    'source': self.data_fetcher.get_source_citation('agriculture_production', {
                        'states': states,
                        'crops': crops,
                        'years': years
                    })
                }
            except Exception as e:
                logger.error(f"Error fetching production data: {e}")
        
        # Fetch district-wise data if needed
        if parsed_query['districts'] or 'district' in parsed_query['original_query'].lower():
            for state in states:
                try:
                    district_df = self.data_fetcher.fetch_district_data(
                        state, crops[0] if crops else None
                    )
                    data_results[f'district_{state}'] = {
                        'dataframe': district_df,
                        'source': self.data_fetcher.get_source_citation('district_wise_crops', {
                            'state': state,
                            'crop': crops[0] if crops else None
                        })
                    }
                except Exception as e:
                    logger.error(f"Error fetching district data: {e}")
        
        return data_results
    
    def _analyze_data(self, parsed_query: Dict, data_results: Dict) -> Dict[str, Any]:
        """Perform analysis based on query intent"""
        intent = parsed_query['intent']
        
        if intent == 'compare':
            return self.analytics.compare_analysis(parsed_query, data_results)
        elif intent == 'top':
            return self.analytics.top_n_analysis(parsed_query, data_results)
        elif intent == 'trend':
            return self.analytics.trend_analysis(parsed_query, data_results)
        elif intent == 'correlation':
            return self.analytics.correlation_analysis(parsed_query, data_results)
        else:
            return self.analytics.general_analysis(parsed_query, data_results)
    
    def _generate_visualizations(self, parsed_query: Dict, analysis_results: Dict) -> List:
        """Generate appropriate visualizations"""
        return self.visualizer.create_visualizations(parsed_query, analysis_results)
    
    def _generate_answer(self, parsed_query: Dict, analysis_results: Dict) -> str:
        """Generate natural language answer"""
        intent = parsed_query['intent']
        
        if intent == 'compare':
            return self._generate_comparison_answer(parsed_query, analysis_results)
        elif intent == 'top':
            return self._generate_top_n_answer(parsed_query, analysis_results)
        elif intent == 'trend':
            return self._generate_trend_answer(parsed_query, analysis_results)
        else:
            return self._generate_general_answer(parsed_query, analysis_results)
    
    def _generate_comparison_answer(self, parsed_query: Dict, analysis: Dict) -> str:
        """Generate answer for comparison queries"""
        states = parsed_query['states']
        
        if not analysis.get('summary'):
            return "I found limited data for this comparison. Please try a different query."
        
        answer_parts = ["Based on the analysis of data from data.gov.in:\n\n"]
        
        if 'rainfall_comparison' in analysis['summary']:
            rainfall_data = analysis['summary']['rainfall_comparison']
            answer_parts.append("**Rainfall Comparison:**\n")
            for state, value in rainfall_data.items():
                answer_parts.append(f"- {state}: {value:.1f} mm average annual rainfall\n")
            answer_parts.append("\n")
        
        if 'crop_comparison' in analysis['summary']:
            crop_data = analysis['summary']['crop_comparison']
            answer_parts.append("**Top Crops by State:**\n")
            for state, crops in crop_data.items():
                answer_parts.append(f"\n*{state}:*\n")
                for i, crop_info in enumerate(crops[:3], 1):
                    answer_parts.append(f"  {i}. {crop_info['crop']}: {crop_info['production']:,.0f} tonnes\n")
        
        return "".join(answer_parts)
    
    def _generate_top_n_answer(self, parsed_query: Dict, analysis: Dict) -> str:
        """Generate answer for top-N queries"""
        top_n = parsed_query['top_n']
        
        if not analysis.get('top_results'):
            return f"No data available for top {top_n} analysis."
        
        answer = f"**Top {top_n} Results:**\n\n"
        
        for i, item in enumerate(analysis['top_results'][:top_n], 1):
            answer += f"{i}. {item['name']}: {item['value']:,.1f} {item.get('unit', '')}\n"
        
        return answer
    
    def _generate_trend_answer(self, parsed_query: Dict, analysis: Dict) -> str:
        """Generate answer for trend analysis queries"""
        if not analysis.get('trend_summary'):
            return "Insufficient data for trend analysis."
        
        trend = analysis['trend_summary']
        answer = "**Trend Analysis:**\n\n"
        answer += f"- Overall trend: {trend.get('direction', 'stable')}\n"
        answer += f"- Average growth rate: {trend.get('growth_rate', 0):.2f}% per year\n"
        answer += f"- Period covered: {trend.get('start_year', 'N/A')} to {trend.get('end_year', 'N/A')}\n"
        
        return answer
    
    def _generate_general_answer(self, parsed_query: Dict, analysis: Dict) -> str:
        """Generate answer for general queries"""
        if not analysis.get('summary'):
            return "I found some data but couldn't generate a comprehensive answer. Please refine your query."
        
        summary = analysis.get('summary', {})
        answer_parts = ["**Analysis Results:**\n\n"]
        
        # Handle rainfall data
        if 'rainfall' in summary:
            rainfall_info = summary['rainfall']
            answer_parts.append("**Rainfall Information:**\n")
            
            if 'record_count' in rainfall_info:
                answer_parts.append(f"- Total records analyzed: {rainfall_info['record_count']}\n")
            
            # Extract statistics
            if 'annual_rainfall_mm_stats' in rainfall_info:
                stats = rainfall_info['annual_rainfall_mm_stats']
                answer_parts.append(f"- Average annual rainfall: {stats['mean']:.1f} mm\n")
                answer_parts.append(f"- Highest recorded rainfall: {stats['max']:.1f} mm\n")
                answer_parts.append(f"- Lowest recorded rainfall: {stats['min']:.1f} mm\n")
                answer_parts.append(f"- Median rainfall: {stats['median']:.1f} mm\n\n")
            
            # Show sample data
            if 'sample_data' in rainfall_info and rainfall_info['sample_data']:
                answer_parts.append("**Recent Data Points:**\n")
                for i, record in enumerate(rainfall_info['sample_data'][:3], 1):
                    state = record.get('state', 'N/A')
                    year = record.get('year', 'N/A')
                    rainfall = record.get('annual_rainfall_mm', 0)
                    answer_parts.append(f"{i}. {state} ({year}): {rainfall:.1f} mm\n")
                answer_parts.append("\n")
        
        # Handle production data
        if 'production' in summary:
            prod_info = summary['production']
            answer_parts.append("**Crop Production Information:**\n")
            
            if 'record_count' in prod_info:
                answer_parts.append(f"- Total production records: {prod_info['record_count']}\n")
            
            # Extract statistics
            if 'production_tonnes_stats' in prod_info:
                stats = prod_info['production_tonnes_stats']
                answer_parts.append(f"- Average production: {stats['mean']:,.0f} tonnes\n")
                answer_parts.append(f"- Highest production: {stats['max']:,.0f} tonnes\n")
                answer_parts.append(f"- Lowest production: {stats['min']:,.0f} tonnes\n\n")
            
            # Show sample data
            if 'sample_data' in prod_info and prod_info['sample_data']:
                answer_parts.append("**Top Production Records:**\n")
                for i, record in enumerate(prod_info['sample_data'][:3], 1):
                    state = record.get('state', 'N/A')
                    crop = record.get('crop', 'N/A')
                    year = record.get('year', 'N/A')
                    prod = record.get('production_tonnes', 0)
                    answer_parts.append(f"{i}. {crop} in {state} ({year}): {prod:,.0f} tonnes\n")
                answer_parts.append("\n")
        
        # Handle district data
        for key, value in summary.items():
            if key.startswith('district_'):
                state_name = key.replace('district_', '').replace('_', ' ')
                answer_parts.append(f"**District-wise Data for {state_name}:**\n")
                
                if 'record_count' in value:
                    answer_parts.append(f"- Districts analyzed: {value['record_count']}\n")
                
                if 'sample_data' in value and value['sample_data']:
                    answer_parts.append("**Top Districts:**\n")
                    for i, record in enumerate(value['sample_data'][:3], 1):
                        district = record.get('district', 'N/A')
                        crop = record.get('crop', 'N/A')
                        prod = record.get('production_tonnes', 0)
                        answer_parts.append(f"{i}. {district} - {crop}: {prod:,.0f} tonnes\n")
                    answer_parts.append("\n")
        
        result = "".join(answer_parts)
        
        # If no structured data was found, return a simple summary
        if result == "**Analysis Results:**\n\n":
            return f"**Analysis Results:**\n\nI found data for your query with {analysis.get('data_points', 0)} data points. The information includes details about the requested regions and time periods."
        
        return result
    
    def _collect_sources(self, data_results: Dict) -> List[Dict]:
        """Collect all data source citations"""
        sources = []
        
        for key, data_info in data_results.items():
            if isinstance(data_info, dict) and 'source' in data_info:
                sources.append(data_info['source'])
        
        return sources