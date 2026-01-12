#!/usr/bin/env python3
"""Generate a new API key for 3D Print Logger."""

import secrets
import hashlib
from sqlalchemy import create_engine, text
from datetime import datetime, UTC

# Generate new API key
random_part = secrets.token_hex(32)
full_key = f"3dp_{random_part}"
key_hash = hashlib.sha256(full_key.encode()).hexdigest()
key_prefix = full_key[:12]

# Connect to database
engine = create_engine("sqlite:///data/printlog.db")

# Insert new API key
with engine.connect() as conn:
    conn.execute(text("""
        INSERT INTO api_keys (key_hash, key_prefix, name, is_active, created_at, updated_at)
        VALUES (:key_hash, :key_prefix, :name, 1, :now, :now)
    """), {
        "key_hash": key_hash,
        "key_prefix": key_prefix,
        "name": "bootstrap",
        "now": datetime.now(UTC)
    })
    conn.commit()

print("\n" + "="*60)
print("NEW API KEY CREATED")
print("="*60)
print(f"\nFull API Key: {full_key}")
print(f"Key Prefix:   {key_prefix}")
print(f"\nSave this key securely - it won't be shown again!")
print("="*60 + "\n")
