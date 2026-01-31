#!/usr/bin/env python3
"""Check normalization mappings in database."""

import os
import sys
import warnings
from pathlib import Path
from dotenv import load_dotenv

warnings.filterwarnings('ignore')

project_root = Path(__file__).parent.parent.parent
env_file = project_root / ".env.local"
if not env_file.exists():
    env_file = project_root / ".env"

if env_file.exists():
    load_dotenv(env_file)

script_dir = Path(__file__).parent
backend_path = script_dir.parent
sys.path.insert(0, str(backend_path))
os.chdir(backend_path)

from database.property_repository import PropertyRepository

repo = PropertyRepository()
mappings = repo.client.table('amenity_normalizations').select('*').order('created_at', desc=True).limit(10).execute()

print(f'Found {len(mappings.data)} normalization mappings in database:\n')
for m in mappings.data:
    conf = m.get('confidence_score', 'N/A')
    if isinstance(conf, float):
        conf = f"{conf:.2f}"
    print(f"  {m['raw_name']:35} → {m['normalized_name']:25} ({m['category']:9}) conf: {conf}")
