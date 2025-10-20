#!/usr/bin/env python
"""
Test MongoDB Atlas connection locally
Run: python test_mongodb_atlas.py
"""
import os
import sys
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, OperationFailure

# Test connection string - UPDATE THIS WITH YOUR ACTUAL CREDENTIALS
MONGODB_URL = os.getenv('MONGODB_URL', 'mongodb+srv://mindnotes_user:mindnotes%401234@cluster0.aibpsrl.mongodb.net/mindnotes?retryWrites=true&w=majority')

print("=" * 60)
print("MongoDB Atlas Connection Test")
print("=" * 60)
print()

# Parse and display connection info (hide password)
if '@' in MONGODB_URL:
    parts = MONGODB_URL.split('@')
    creds = parts[0].split('://')[-1]
    host_part = parts[1] if len(parts) > 1 else 'unknown'
    username = creds.split(':')[0] if ':' in creds else 'unknown'
    print(f"📍 Cluster: {host_part.split('/')[0]}")
    print(f"👤 Username: {username}")
    print(f"🔐 Password: {'*' * 10} (hidden)")
    print()

print("🔌 Attempting to connect...")
print()

try:
    # Create client
    client = MongoClient(
        MONGODB_URL,
        serverSelectionTimeoutMS=5000,  # 5 second timeout
        connectTimeoutMS=5000
    )

    # Test connection
    print("✅ Client created successfully")

    # Try to ping
    client.admin.command('ping')
    print("✅ Ping successful - connection working!")

    # List databases
    dbs = client.list_database_names()
    print(f"✅ Databases accessible: {dbs}")

    # Test specific database
    db = client['mindnotes']
    collections = db.list_collection_names()
    print(f"✅ Collections in 'mindnotes' database: {collections if collections else 'None (empty)'}")

    print()
    print("=" * 60)
    print("🎉 SUCCESS! MongoDB Atlas connection is working!")
    print("=" * 60)

except OperationFailure as e:
    print()
    print("=" * 60)
    print("❌ AUTHENTICATION FAILED")
    print("=" * 60)
    print()
    print(f"Error: {e}")
    print()
    print("🔍 Possible issues:")
    print("  1. Wrong username or password")
    print("  2. User doesn't exist in MongoDB Atlas")
    print("  3. Password has special characters that need URL encoding")
    print()
    print("📋 How to fix:")
    print("  1. Go to: https://cloud.mongodb.com")
    print("  2. Click 'Database Access' → Check username")
    print("  3. Edit user or create new one")
    print("  4. Copy the correct password")
    print("  5. URL-encode special characters:")
    print("     @ → %40")
    print("     : → %3A")
    print("     / → %2F")
    print("     # → %23")
    print("     ! → %21")
    print()
    sys.exit(1)

except ConnectionFailure as e:
    print()
    print("=" * 60)
    print("❌ CONNECTION FAILED")
    print("=" * 60)
    print()
    print(f"Error: {e}")
    print()
    print("🔍 Possible issues:")
    print("  1. Network/firewall blocking connection")
    print("  2. MongoDB Atlas IP whitelist doesn't include your IP")
    print("  3. Cluster is paused or deleted")
    print()
    print("📋 How to fix:")
    print("  1. Go to: https://cloud.mongodb.com")
    print("  2. Click 'Network Access'")
    print("  3. Add IP Address: 0.0.0.0/0 (allow all)")
    print("  4. Check cluster status is 'Active'")
    print()
    sys.exit(1)

except Exception as e:
    print()
    print("=" * 60)
    print("❌ UNEXPECTED ERROR")
    print("=" * 60)
    print()
    print(f"Error type: {type(e).__name__}")
    print(f"Error message: {e}")
    print()
    import traceback
    traceback.print_exc()
    print()
    sys.exit(1)
