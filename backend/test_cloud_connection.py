#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from database.supabase_client import get_supabase_client

def test_connection():
    try:
        print("Testing Supabase cloud connection...")
        supabase = get_supabase_client()
        print("✓ Client initialized")

        response = supabase.table('properties').select('id', count='exact').execute()
        print(f"✓ Database query successful")
        print(f"  Property count: {response.count}")
        return True
    except Exception as e:
        print(f"✗ Connection failed: {e}")
        return False

if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)
