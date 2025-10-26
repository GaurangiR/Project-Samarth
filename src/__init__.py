"""
Project Samarth - Source Package
Intelligent Q&A System for Indian Agricultural Economy
"""

__version__ = "1.0.0"
__author__ = "BTech Engineering Candidate"
__description__ = "Intelligent Q&A System over live data.gov.in APIs"

from .config import Config
from .data_fetcher import DataFetcher
from .query_engine import QueryEngine
from .analytics import AnalyticsEngine
from .visualizer import Visualizer

__all__ = [
    'Config',
    'DataFetcher',
    'QueryEngine',
    'AnalyticsEngine',
    'Visualizer'
]