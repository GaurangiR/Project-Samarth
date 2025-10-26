"""
Configuration management for Project Samarth
Handles environment variables, API endpoints, and system settings
"""

import os
from pathlib import Path
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Central configuration class for Project Samarth"""
    
    # Project paths
    BASE_DIR = Path(__file__).parent.parent
    DATA_DIR = BASE_DIR / 'data'
    CACHE_DIR = DATA_DIR / 'cache'
    LOGS_DIR = BASE_DIR / 'logs'
    
    # Create directories if they don't exist
    for directory in [DATA_DIR, CACHE_DIR, LOGS_DIR]:
        directory.mkdir(parents=True, exist_ok=True)
    
    # API Configuration
    DATA_GOV_API_KEY = os.getenv('DATA_GOV_API_KEY', 'YOUR_API_KEY_HERE')
    
    # data.gov.in API Endpoints
    # Note: These are example endpoints. Actual endpoints from data.gov.in should be configured
    API_ENDPOINTS = {
        'imd_rainfall': {
            'base_url': 'https://api.data.gov.in/resource/',
            'resource_id': '9ef84268-d588-465a-a308-a864a43d0070',  # IMD rainfall data
            'name': 'IMD Rainfall Data'
        },
        'agriculture_production': {
            'base_url': 'https://api.data.gov.in/resource/',
            'resource_id': '8d6c8e8e-e9cd-4f42-b37a-6d9f9e1e4c7a',  # Agriculture production
            'name': 'Agricultural Production Statistics'
        },
        'crop_yield': {
            'base_url': 'https://api.data.gov.in/resource/',
            'resource_id': 'a8e8c8d9-f3e1-4b5d-9c7e-1a2b3c4d5e6f',  # Crop yield data
            'name': 'Crop Yield Data'
        },
        'district_wise_crops': {
            'base_url': 'https://api.data.gov.in/resource/',
            'resource_id': 'b7d9f2e3-a1c4-4e8d-b9f2-3c4d5e6f7a8b',  # District-wise crop data
            'name': 'District-wise Crop Production'
        }
    }
    
    # Cache configuration
    CACHE_TTL = 3600  # 1 hour in seconds
    ENABLE_CACHE = True
    
    # Rate limiting
    API_RATE_LIMIT = 100  # requests per hour
    API_TIMEOUT = 30  # seconds
    
    # NLP Configuration
    SPACY_MODEL = 'en_core_web_sm'
    
    # Indian States (for entity recognition)
    INDIAN_STATES = [
        'Andhra Pradesh', 'Arunachal Pradesh', 'Assam', 'Bihar', 'Chhattisgarh',
        'Goa', 'Gujarat', 'Haryana', 'Himachal Pradesh', 'Jharkhand', 'Karnataka',
        'Kerala', 'Madhya Pradesh', 'Maharashtra', 'Manipur', 'Meghalaya', 'Mizoram',
        'Nagaland', 'Odisha', 'Punjab', 'Rajasthan', 'Sikkim', 'Tamil Nadu',
        'Telangana', 'Tripura', 'Uttar Pradesh', 'Uttarakhand', 'West Bengal',
        'Delhi', 'Jammu and Kashmir', 'Ladakh', 'Puducherry', 'Chandigarh',
        'Dadra and Nagar Haveli', 'Daman and Diu', 'Lakshadweep', 
        'Andaman and Nicobar Islands'
    ]
    
    # State abbreviations mapping
    STATE_ABBREVIATIONS = {
        'AP': 'Andhra Pradesh', 'AR': 'Arunachal Pradesh', 'AS': 'Assam',
        'BR': 'Bihar', 'CG': 'Chhattisgarh', 'GA': 'Goa', 'GJ': 'Gujarat',
        'HR': 'Haryana', 'HP': 'Himachal Pradesh', 'JH': 'Jharkhand',
        'KA': 'Karnataka', 'KL': 'Kerala', 'MP': 'Madhya Pradesh',
        'MH': 'Maharashtra', 'MN': 'Manipur', 'ML': 'Meghalaya', 'MZ': 'Mizoram',
        'NL': 'Nagaland', 'OD': 'Odisha', 'PB': 'Punjab', 'RJ': 'Rajasthan',
        'SK': 'Sikkim', 'TN': 'Tamil Nadu', 'TG': 'Telangana', 'TR': 'Tripura',
        'UP': 'Uttar Pradesh', 'UK': 'Uttarakhand', 'WB': 'West Bengal',
        'DL': 'Delhi', 'JK': 'Jammu and Kashmir', 'LA': 'Ladakh', 'PY': 'Puducherry'
    }
    
    # Major crops in India
    MAJOR_CROPS = [
        'Rice', 'Wheat', 'Maize', 'Bajra', 'Jowar', 'Barley', 'Ragi',
        'Cotton', 'Sugarcane', 'Jute', 'Tobacco', 'Tea', 'Coffee',
        'Coconut', 'Groundnut', 'Soybean', 'Sunflower', 'Rapeseed', 'Mustard',
        'Potato', 'Onion', 'Tomato', 'Pulses', 'Chickpea', 'Lentil',
        'Arhar', 'Moong', 'Urad', 'Masoor', 'Fruits', 'Vegetables'
    ]
    
    # Crop categories
    CROP_CATEGORIES = {
        'cereals': ['Rice', 'Wheat', 'Maize', 'Bajra', 'Jowar', 'Barley', 'Ragi'],
        'pulses': ['Chickpea', 'Arhar', 'Moong', 'Urad', 'Lentil', 'Masoor'],
        'oilseeds': ['Groundnut', 'Soybean', 'Sunflower', 'Rapeseed', 'Mustard'],
        'cash_crops': ['Cotton', 'Sugarcane', 'Jute', 'Tobacco', 'Tea', 'Coffee'],
        'horticulture': ['Fruits', 'Vegetables', 'Potato', 'Onion', 'Tomato', 'Coconut']
    }
    
    # Logging configuration
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # Application settings
    APP_NAME = "Project Samarth"
    APP_VERSION = "1.0.0"
    DEBUG_MODE = os.getenv('DEBUG', 'False').lower() == 'true'
    
    @classmethod
    def get_api_url(cls, endpoint_name: str) -> str:
        """Construct full API URL for a given endpoint"""
        endpoint = cls.API_ENDPOINTS.get(endpoint_name)
        if not endpoint:
            raise ValueError(f"Unknown endpoint: {endpoint_name}")
        
        return f"{endpoint['base_url']}{endpoint['resource_id']}"
    
    @classmethod
    def get_api_params(cls, **kwargs) -> Dict[str, Any]:
        """Get standard API parameters including auth"""
        params = {
            'api-key': cls.DATA_GOV_API_KEY,
            'format': 'json',
            'limit': kwargs.get('limit', 1000),
            'offset': kwargs.get('offset', 0)
        }
        
        # Add any additional filters
        for key, value in kwargs.items():
            if key not in ['limit', 'offset'] and value is not None:
                params[f'filters[{key}]'] = value
        
        return params
    
    @classmethod
    def validate_config(cls) -> bool:
        """Validate that required configuration is present"""
        if cls.DATA_GOV_API_KEY == 'YOUR_API_KEY_HERE':
            print("⚠️  Warning: DATA_GOV_API_KEY not configured. Using demo mode.")
            return False
        return True
    
    @classmethod
    def is_demo_mode(cls) -> bool:
        """Check if running in demo mode (without real API keys)"""
        return not cls.validate_config()


# Export configuration instance
config = Config()