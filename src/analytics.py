"""
Analytics Engine for Project Samarth
Performs statistical analysis, aggregations, and data processing
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
from scipy import stats
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AnalyticsEngine:
    """
    Handles all data analytics operations including:
    - Comparative analysis
    - Top-N rankings
    - Trend analysis
    - Correlation studies
    """
    
    def __init__(self):
        self.confidence_threshold = 0.7
    
    def compare_analysis(self, parsed_query: Dict, data_results: Dict) -> Dict[str, Any]:
        """
        Perform comparative analysis across states/crops/regions
        """
        summary = {}
        data_points = 0
        
        # Rainfall comparison
        if 'rainfall' in data_results:
            rainfall_df = data_results['rainfall']['dataframe']
            if not rainfall_df.empty:
                # Calculate average rainfall by state
                rainfall_avg = rainfall_df.groupby('state')['annual_rainfall_mm'].mean()
                summary['rainfall_comparison'] = rainfall_avg.to_dict()
                data_points += len(rainfall_df)
        
        # Crop production comparison
        if 'production' in data_results:
            production_df = data_results['production']['dataframe']
            if not production_df.empty:
                # Get top crops by state
                crop_summary = {}
                for state in production_df['state'].unique():
                    state_data = production_df[production_df['state'] == state]
                    top_crops = state_data.groupby('crop')['production_tonnes'].sum().sort_values(ascending=False)
                    crop_summary[state] = [
                        {'crop': crop, 'production': prod} 
                        for crop, prod in top_crops.head(5).items()
                    ]
                summary['crop_comparison'] = crop_summary
                data_points += len(production_df)
        
        return {
            'summary': summary,
            'data': data_results,
            'confidence': self._calculate_confidence(data_points),
            'data_points': data_points
        }
    
    def top_n_analysis(self, parsed_query: Dict, data_results: Dict) -> Dict[str, Any]:
        """
        Find top N items based on specified metric
        """
        top_n = parsed_query['top_n']
        top_results = []
        data_points = 0
        
        if 'production' in data_results:
            production_df = data_results['production']['dataframe']
            if not production_df.empty:
                # Aggregate by crop across all states
                crop_totals = production_df.groupby('crop')['production_tonnes'].sum().sort_values(ascending=False)
                
                for crop, production in crop_totals.head(top_n).items():
                    top_results.append({
                        'name': crop,
                        'value': production,
                        'unit': 'tonnes'
                    })
                data_points = len(production_df)
        
        # If production data not available, try rainfall
        elif 'rainfall' in data_results:
            rainfall_df = data_results['rainfall']['dataframe']
            if not rainfall_df.empty:
                state_rainfall = rainfall_df.groupby('state')['annual_rainfall_mm'].mean().sort_values(ascending=False)
                
                for state, rainfall in state_rainfall.head(top_n).items():
                    top_results.append({
                        'name': state,
                        'value': rainfall,
                        'unit': 'mm'
                    })
                data_points = len(rainfall_df)
        
        return {
            'top_results': top_results,
            'data': data_results,
            'confidence': self._calculate_confidence(data_points),
            'data_points': data_points
        }
    
    def trend_analysis(self, parsed_query: Dict, data_results: Dict) -> Dict[str, Any]:
        """
        Analyze trends over time
        """
        trend_summary = {}
        data_points = 0
        
        # Production trends
        if 'production' in data_results:
            production_df = data_results['production']['dataframe']
            if not production_df.empty and 'year' in production_df.columns:
                # Calculate year-over-year growth
                yearly_total = production_df.groupby('year')['production_tonnes'].sum().sort_index()
                
                if len(yearly_total) > 1:
                    # Calculate growth rate
                    growth_rates = yearly_total.pct_change() * 100
                    avg_growth = growth_rates.mean()
                    
                    # Determine trend direction
                    if avg_growth > 2:
                        direction = "increasing"
                    elif avg_growth < -2:
                        direction = "decreasing"
                    else:
                        direction = "stable"
                    
                    trend_summary = {
                        'direction': direction,
                        'growth_rate': avg_growth,
                        'start_year': int(yearly_total.index[0]),
                        'end_year': int(yearly_total.index[-1]),
                        'start_value': float(yearly_total.iloc[0]),
                        'end_value': float(yearly_total.iloc[-1]),
                        'yearly_data': yearly_total.to_dict()
                    }
                    data_points = len(production_df)
        
        # Rainfall trends
        elif 'rainfall' in data_results:
            rainfall_df = data_results['rainfall']['dataframe']
            if not rainfall_df.empty and 'year' in rainfall_df.columns:
                yearly_rainfall = rainfall_df.groupby('year')['annual_rainfall_mm'].mean().sort_index()
                
                if len(yearly_rainfall) > 1:
                    growth_rates = yearly_rainfall.pct_change() * 100
                    avg_growth = growth_rates.mean()
                    
                    direction = "increasing" if avg_growth > 1 else ("decreasing" if avg_growth < -1 else "stable")
                    
                    trend_summary = {
                        'direction': direction,
                        'growth_rate': avg_growth,
                        'start_year': int(yearly_rainfall.index[0]),
                        'end_year': int(yearly_rainfall.index[-1]),
                        'start_value': float(yearly_rainfall.iloc[0]),
                        'end_value': float(yearly_rainfall.iloc[-1]),
                        'yearly_data': yearly_rainfall.to_dict()
                    }
                    data_points = len(rainfall_df)
        
        return {
            'trend_summary': trend_summary,
            'data': data_results,
            'confidence': self._calculate_confidence(data_points),
            'data_points': data_points
        }
    
    def correlation_analysis(self, parsed_query: Dict, data_results: Dict) -> Dict[str, Any]:
        """
        Analyze correlations between rainfall and crop production
        """
        correlation_results = {}
        data_points = 0
        
        if 'rainfall' in data_results and 'production' in data_results:
            rainfall_df = data_results['rainfall']['dataframe']
            production_df = data_results['production']['dataframe']
            
            if not rainfall_df.empty and not production_df.empty:
                # Merge data on state and year
                if 'year' in rainfall_df.columns and 'year' in production_df.columns:
                    merged = pd.merge(
                        rainfall_df,
                        production_df,
                        on=['state', 'year'],
                        how='inner'
                    )
                    
                    if len(merged) > 5:  # Need minimum data points for correlation
                        # Calculate correlation
                        corr_coef, p_value = stats.pearsonr(
                            merged['annual_rainfall_mm'],
                            merged['production_tonnes']
                        )
                        
                        correlation_results = {
                            'correlation_coefficient': float(corr_coef),
                            'p_value': float(p_value),
                            'significance': 'significant' if p_value < 0.05 else 'not significant',
                            'interpretation': self._interpret_correlation(corr_coef),
                            'sample_size': len(merged)
                        }
                        data_points = len(merged)
        
        return {
            'correlation_results': correlation_results,
            'data': data_results,
            'confidence': self._calculate_confidence(data_points),
            'data_points': data_points
        }
    
    def general_analysis(self, parsed_query: Dict, data_results: Dict) -> Dict[str, Any]:
        """
        Perform general analysis and summarization
        """
        summary = {}
        data_points = 0
        
        for key, data_info in data_results.items():
            if isinstance(data_info, dict) and 'dataframe' in data_info:
                df = data_info['dataframe']
                if not df.empty:
                    # Basic statistics
                    summary[key] = {
                        'record_count': len(df),
                        'columns': list(df.columns),
                        'sample_data': df.head(5).to_dict('records')
                    }
                    
                    # Add numeric column statistics
                    numeric_cols = df.select_dtypes(include=[np.number]).columns
                    for col in numeric_cols:
                        summary[key][f'{col}_stats'] = {
                            'mean': float(df[col].mean()),
                            'median': float(df[col].median()),
                            'min': float(df[col].min()),
                            'max': float(df[col].max()),
                            'std': float(df[col].std())
                        }
                    
                    data_points += len(df)
        
        return {
            'summary': summary,
            'data': data_results,
            'confidence': self._calculate_confidence(data_points),
            'data_points': data_points
        }
    
    def district_analysis(self, parsed_query: Dict, data_results: Dict) -> Dict[str, Any]:
        """
        Analyze district-level data
        """
        district_summary = {}
        data_points = 0
        
        for key, data_info in data_results.items():
            if 'district' in key and isinstance(data_info, dict):
                df = data_info['dataframe']
                if not df.empty and 'district' in df.columns:
                    # Find highest and lowest producing districts
                    if 'production_tonnes' in df.columns:
                        highest = df.loc[df['production_tonnes'].idxmax()]
                        lowest = df.loc[df['production_tonnes'].idxmin()]
                        
                        district_summary[key] = {
                            'highest_district': {
                                'name': highest['district'],
                                'production': float(highest['production_tonnes']),
                                'crop': highest.get('crop', 'N/A')
                            },
                            'lowest_district': {
                                'name': lowest['district'],
                                'production': float(lowest['production_tonnes']),
                                'crop': lowest.get('crop', 'N/A')
                            },
                            'average_production': float(df['production_tonnes'].mean()),
                            'total_districts': len(df['district'].unique())
                        }
                        data_points += len(df)
        
        return {
            'district_summary': district_summary,
            'data': data_results,
            'confidence': self._calculate_confidence(data_points),
            'data_points': data_points
        }
    
    def _calculate_confidence(self, data_points: int) -> float:
        """
        Calculate confidence score based on data availability
        """
        if data_points == 0:
            return 0.0
        elif data_points < 10:
            return 0.5
        elif data_points < 50:
            return 0.7
        elif data_points < 100:
            return 0.85
        else:
            return 0.95
    
    def _interpret_correlation(self, corr_coef: float) -> str:
        """
        Interpret correlation coefficient
        """
        abs_corr = abs(corr_coef)
        
        if abs_corr > 0.7:
            strength = "strong"
        elif abs_corr > 0.4:
            strength = "moderate"
        elif abs_corr > 0.2:
            strength = "weak"
        else:
            strength = "very weak"
        
        direction = "positive" if corr_coef > 0 else "negative"
        
        return f"{strength} {direction} correlation"
    
    def aggregate_by_period(self, df: pd.DataFrame, period: str = 'year') -> pd.DataFrame:
        """
        Aggregate data by time period
        """
        if period not in df.columns:
            return df
        
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        agg_dict = {col: 'sum' for col in numeric_cols if col != period}
        
        return df.groupby(period).agg(agg_dict).reset_index()
    
    def calculate_growth_rate(self, df: pd.DataFrame, value_col: str, time_col: str = 'year') -> pd.DataFrame:
        """
        Calculate year-over-year growth rates
        """
        if time_col not in df.columns or value_col not in df.columns:
            return df
        
        df = df.sort_values(time_col)
        df['growth_rate'] = df[value_col].pct_change() * 100
        
        return df
    
    def normalize_data(self, df: pd.DataFrame, columns: List[str]) -> pd.DataFrame:
        """
        Normalize specified columns using min-max scaling
        """
        for col in columns:
            if col in df.columns and pd.api.types.is_numeric_dtype(df[col]):
                min_val = df[col].min()
                max_val = df[col].max()
                if max_val > min_val:
                    df[f'{col}_normalized'] = (df[col] - min_val) / (max_val - min_val)
        
        return df
    
    def detect_outliers(self, df: pd.DataFrame, column: str, threshold: float = 3.0) -> pd.DataFrame:
        """
        Detect outliers using z-score method
        """
        if column not in df.columns or not pd.api.types.is_numeric_dtype(df[column]):
            return df
        
        z_scores = np.abs(stats.zscore(df[column].dropna()))
        df['is_outlier'] = False
        df.loc[df[column].notna(), 'is_outlier'] = z_scores > threshold
        
        return df