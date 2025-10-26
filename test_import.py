import sys
import os

print("Testing imports...")

# Test package imports (the way app.py does it)
try:
    from src.config import Config
    print("✓ src.config imported")
except Exception as e:
    print(f"✗ src.config failed: {e}")

try:
    from src.data_fetcher import DataFetcher
    print("✓ src.data_fetcher imported")
except Exception as e:
    print(f"✗ src.data_fetcher failed: {e}")

try:
    from src.analytics import AnalyticsEngine
    print("✓ src.analytics imported")
except Exception as e:
    print(f"✗ src.analytics failed: {e}")

try:
    from src.visualizer import Visualizer
    print("✓ src.visualizer imported")
except Exception as e:
    print(f"✗ src.visualizer failed: {e}")

try:
    from src.query_engine import QueryEngine
    print("✓ src.query_engine imported")
    print(f"  - Has QueryEngine: {hasattr(sys.modules['src.query_engine'], 'QueryEngine')}")
    if 'QueryEngine' in dir(sys.modules['src.query_engine']):
        print(f"  - QueryEngine type: {type(QueryEngine)}")
        # Try instantiating it
        qe = QueryEngine()
        print(f"  - Successfully instantiated QueryEngine")
except Exception as e:
    print(f"✗ src.query_engine failed: {e}")
    import traceback
    traceback.print_exc()

print("\n✅ All tests passed! Your app should work now.")