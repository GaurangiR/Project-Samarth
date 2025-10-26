"""
Data Fetcher Module for Project Samarth
Handles API calls to data.gov.in, caching, and data retrieval
"""

import requests
import json
import hashlib
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import pandas as pd
import logging

from src.config import Config
# Setup logging
logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL),
    format=Config.LOG_FORMAT
)
logger = logging.getLogger(__name__)


class DataFetcher:
    """Handles data fetching from data.gov.in APIs with caching and error handling"""
    
    def __init__(self):
        self.config = Config()
        self.cache_dir = self.config.CACHE_DIR
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': f'{Config.APP_NAME}/{Config.APP_VERSION}',
            'Accept': 'application/json'
        })
        
        # Request tracking for rate limiting
        self.request_times: List[float] = []
    
    def _get_cache_key(self, endpoint: str, params: Dict) -> str:
        """Generate cache key from endpoint and parameters"""
        cache_str = f"{endpoint}_{json.dumps(params, sort_keys=True)}"
        return hashlib.md5(cache_str.encode()).hexdigest()
    
    def _get_cache_path(self, cache_key: str) -> Path:
        """Get cache file path for a given key"""
        return self.cache_dir / f"{cache_key}.json"
    
    def _is_cache_valid(self, cache_path: Path) -> bool:
        """Check if cache file exists and is still valid"""
        if not cache_path.exists():
            return False
        
        if not self.config.ENABLE_CACHE:
            return False
        
        # Check if cache has expired
        cache_age = time.time() - cache_path.stat().st_mtime
        return cache_age < self.config.CACHE_TTL
    
    def _read_cache(self, cache_path: Path) -> Optional[Dict]:
        """Read data from cache file"""
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error reading cache: {e}")
            return None
    
    def _write_cache(self, cache_path: Path, data: Dict):
        """Write data to cache file"""
        try:
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            logger.info(f"Cached data to {cache_path}")
        except Exception as e:
            logger.error(f"Error writing cache: {e}")
    
    def _check_rate_limit(self):
        """Check and enforce rate limiting"""
        now = time.time()
        # Remove requests older than 1 hour
        self.request_times = [t for t in self.request_times if now - t < 3600]
        
        if len(self.request_times) >= self.config.API_RATE_LIMIT:
            oldest_request = min(self.request_times)
            wait_time = 3600 - (now - oldest_request)
            if wait_time > 0:
                logger.warning(f"Rate limit reached. Waiting {wait_time:.0f}s")
                time.sleep(wait_time)
    
    def fetch_data(self, endpoint_name: str, **filters) -> Dict[str, Any]:
        """
        Fetch data from data.gov.in API with caching
        
        Args:
            endpoint_name: Name of the endpoint (from Config.API_ENDPOINTS)
            **filters: Additional filter parameters
        
        Returns:
            Dict containing data and metadata
        """
        # Get API URL and params
        try:
            url = self.config.get_api_url(endpoint_name)
            params = self.config.get_api_params(**filters)
        except ValueError as e:
            logger.error(f"Invalid endpoint: {e}")
            return self._get_demo_data(endpoint_name, filters)
        
        # Check cache
        cache_key = self._get_cache_key(endpoint_name, params)
        cache_path = self._get_cache_path(cache_key)
        
        if self._is_cache_valid(cache_path):
            logger.info(f"Using cached data for {endpoint_name}")
            cached_data = self._read_cache(cache_path)
            if cached_data:
                cached_data['from_cache'] = True
                return cached_data
        
        # Demo mode check
        if self.config.is_demo_mode():
            logger.info("Running in demo mode - using synthetic data")
            return self._get_demo_data(endpoint_name, filters)
        
        # Fetch from API
        try:
            # Check rate limit
            self._check_rate_limit()
            
            logger.info(f"Fetching data from {endpoint_name}")
            response = self.session.get(
                url,
                params=params,
                timeout=self.config.API_TIMEOUT
            )
            response.raise_for_status()
            
            # Record request time
            self.request_times.append(time.time())
            
            # Parse response
            data = response.json()
            
            # Prepare result with metadata
            result = {
                'data': data,
                'endpoint': endpoint_name,
                'url': url,
                'parameters': params,
                'timestamp': datetime.now().isoformat(),
                'from_cache': False,
                'records_count': len(data.get('records', [])) if isinstance(data, dict) else len(data)
            }
            
            # Cache the result
            self._write_cache(cache_path, result)
            
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            # Try to return cached data even if expired
            if cache_path.exists():
                logger.info("Using expired cache due to API error")
                cached_data = self._read_cache(cache_path)
                if cached_data:
                    cached_data['from_cache'] = True
                    cached_data['cache_expired'] = True
                    return cached_data
            
            # Fall back to demo data
            logger.info("Falling back to demo data")
            return self._get_demo_data(endpoint_name, filters)
    
    def _get_demo_data(self, endpoint_name: str, filters: Dict) -> Dict[str, Any]:
        """
        Generate realistic demo data for testing without API keys
        This simulates the structure of data.gov.in responses
        """
        logger.info(f"Generating demo data for {endpoint_name}")
        
        if endpoint_name == 'imd_rainfall':
            # Demo rainfall data
            records = []
            states = filters.get('state', 'Punjab,Haryana').split(',')
            years = range(2018, 2024)
            
            for state in states:
                for year in years:
                    # Simulate realistic rainfall patterns
                    base_rainfall = 1200 if state.strip() == 'Punjab' else 1100
                    records.append({
                        'state': state.strip(),
                        'year': year,
                        'annual_rainfall_mm': base_rainfall + (year - 2018) * 50 + (hash(state) % 200 - 100),
                        'monsoon_rainfall_mm': base_rainfall * 0.7,
                        'district': f"{state.strip()}_District_1"
                    })
            
            return {
                'data': {'records': records},
                'endpoint': endpoint_name,
                'url': 'demo://imd_rainfall',
                'parameters': filters,
                'timestamp': datetime.now().isoformat(),
                'from_cache': False,
                'demo_mode': True,
                'records_count': len(records)
            }
        
        elif endpoint_name == 'agriculture_production':
            # Demo agricultural production data
            records = []
            states = filters.get('state', 'Punjab,Haryana,Maharashtra').split(',')
            crops = ['Rice', 'Wheat', 'Cotton', 'Sugarcane', 'Maize']
            years = range(2018, 2024)
            
            for state in states:
                for crop in crops:
                    for year in years:
                        # Simulate realistic production patterns
                        base_prod = {
                            'Rice': 5000, 'Wheat': 6000, 'Cotton': 3000,
                            'Sugarcane': 8000, 'Maize': 4000
                        }.get(crop, 3000)
                        
                        production = base_prod + (year - 2018) * 200 + (hash(f"{state}{crop}") % 1000)
                        
                        records.append({
                            'state': state.strip(),
                            'crop': crop,
                            'year': year,
                            'production_tonnes': production,
                            'area_hectares': production / 2.5,
                            'yield_kg_per_hectare': 2500
                        })
            
            return {
                'data': {'records': records},
                'endpoint': endpoint_name,
                'url': 'demo://agriculture_production',
                'parameters': filters,
                'timestamp': datetime.now().isoformat(),
                'from_cache': False,
                'demo_mode': True,
                'records_count': len(records)
            }
        
        elif endpoint_name == 'district_wise_crops':
            # Demo district-wise crop data
            records = []
            state = filters.get('state', 'Uttar Pradesh')
            districts = [f"{state}_District_{i}" for i in range(1, 6)]
            crops = ['Wheat', 'Rice', 'Sugarcane', 'Potato']
            
            for district in districts:
                for crop in crops:
                    production = 1000 + (hash(f"{district}{crop}") % 5000)
                    records.append({
                        'state': state,
                        'district': district,
                        'crop': crop,
                        'production_tonnes': production,
                        'year': 2023
                    })
            
            return {
                'data': {'records': records},
                'endpoint': endpoint_name,
                'url': 'demo://district_wise_crops',
                'parameters': filters,
                'timestamp': datetime.now().isoformat(),
                'from_cache': False,
                'demo_mode': True,
                'records_count': len(records)
            }
        
        else:
            # Generic demo data
            return {
                'data': {'records': []},
                'endpoint': endpoint_name,
                'url': f'demo://{endpoint_name}',
                'parameters': filters,
                'timestamp': datetime.now().isoformat(),
                'from_cache': False,
                'demo_mode': True,
                'records_count': 0
            }
    
    def fetch_rainfall_data(self, states: List[str], years: Optional[List[int]] = None) -> pd.DataFrame:
        """
        Fetch rainfall data for specific states and years
        
        Args:
            states: List of state names
            years: Optional list of years (defaults to last 5 years)
        
        Returns:
            DataFrame with rainfall data
        """
        if years is None:
            current_year = datetime.now().year
            years = list(range(current_year - 5, current_year))
        
        filters = {
            'state': ','.join(states),
            'year': ','.join(map(str, years))
        }
        
        result = self.fetch_data('imd_rainfall', **filters)
        
        if result['records_count'] > 0:
            df = pd.DataFrame(result['data']['records'])
            return df
        else:
            return pd.DataFrame()
    
    def fetch_crop_production(self, states: List[str], crops: Optional[List[str]] = None,
                             years: Optional[List[int]] = None) -> pd.DataFrame:
        """
        Fetch crop production data
        
        Args:
            states: List of state names
            crops: Optional list of crop names
            years: Optional list of years
        
        Returns:
            DataFrame with production data
        """
        filters = {'state': ','.join(states)}
        
        if crops:
            filters['crop'] = ','.join(crops)
        if years:
            filters['year'] = ','.join(map(str, years))
        
        result = self.fetch_data('agriculture_production', **filters)
        
        if result['records_count'] > 0:
            df = pd.DataFrame(result['data']['records'])
            return df
        else:
            return pd.DataFrame()
    
    def fetch_district_data(self, state: str, crop: Optional[str] = None) -> pd.DataFrame:
        """
        Fetch district-wise crop data
        
        Args:
            state: State name
            crop: Optional crop name filter
        
        Returns:
            DataFrame with district-wise data
        """
        filters = {'state': state}
        if crop:
            filters['crop'] = crop
        
        result = self.fetch_data('district_wise_crops', **filters)
        
        if result['records_count'] > 0:
            df = pd.DataFrame(result['data']['records'])
            return df
        else:
            return pd.DataFrame()
    
    def check_api_status(self) -> Dict[str, bool]:
        """
        Check connectivity status of all configured APIs
        
        Returns:
            Dict mapping endpoint names to connection status
        """
        status = {}
        
        for endpoint_name in self.config.API_ENDPOINTS.keys():
            try:
                # Try a minimal fetch
                result = self.fetch_data(endpoint_name, limit=1)
                status[endpoint_name] = not result.get('demo_mode', False)
            except Exception as e:
                logger.error(f"Status check failed for {endpoint_name}: {e}")
                status[endpoint_name] = False
        
        return status
    
    def get_source_citation(self, endpoint_name: str, parameters: Dict) -> Dict[str, Any]:
        """
        Generate a citation for data source
        
        Args:
            endpoint_name: Name of the data endpoint
            parameters: Parameters used in the request
        
        Returns:
            Citation dictionary
        """
        endpoint_info = self.config.API_ENDPOINTS.get(endpoint_name, {})
        
        return {
            'name': endpoint_info.get('name', endpoint_name),
            'endpoint': endpoint_name,
            'url': self.config.get_api_url(endpoint_name) if not self.config.is_demo_mode() else f"demo://{endpoint_name}",
            'parameters': parameters,
            'timestamp': datetime.now().isoformat(),
            'source': 'data.gov.in Open Government Data Platform',
            'provider': endpoint_info.get('provider', 'Government of India')
        }
    
    def clear_cache(self, endpoint_name: Optional[str] = None):
        """
        Clear cached data
        
        Args:
            endpoint_name: Optional specific endpoint to clear (clears all if None)
        """
        if endpoint_name:
            # Clear specific endpoint cache
            for cache_file in self.cache_dir.glob(f"*{endpoint_name}*.json"):
                cache_file.unlink()
                logger.info(f"Cleared cache: {cache_file}")
        else:
            # Clear all cache
            for cache_file in self.cache_dir.glob("*.json"):
                cache_file.unlink()
            logger.info("Cleared all cache files")