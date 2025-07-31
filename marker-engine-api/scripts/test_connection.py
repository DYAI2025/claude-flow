#!/usr/bin/env python3
"""
Test MongoDB connection and display database information
"""

import os
import sys
from pymongo import MongoClient
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "marker_engine")

if not DATABASE_URL:
    print("❌ DATABASE_URL not found in environment")
    print("Please create a .env file with your MongoDB connection string")
    sys.exit(1)

print("🔍 Testing MongoDB Connection...")
print("=" * 50)

try:
    # Connect to MongoDB
    client = MongoClient(DATABASE_URL, serverSelectionTimeoutMS=5000)
    
    # Test connection
    server_info = client.server_info()
    print("✅ Successfully connected to MongoDB!")
    print(f"   Server version: {server_info.get('version', 'Unknown')}")
    
    # Access database
    db = client[MONGO_DB_NAME]
    print(f"\n📊 Database: {MONGO_DB_NAME}")
    
    # List collections
    collections = db.list_collection_names()
    print(f"\n📁 Collections ({len(collections)}):")
    
    for collection_name in collections:
        collection = db[collection_name]
        count = collection.count_documents({})
        
        # Get indexes
        indexes = list(collection.list_indexes())
        index_names = [idx['name'] for idx in indexes if idx['name'] != '_id_']
        
        print(f"\n   • {collection_name}:")
        print(f"     - Documents: {count}")
        print(f"     - Indexes: {', '.join(index_names) if index_names else 'none (only _id_)'}")
        
        # Check validation
        if collection_name == "markers":
            coll_info = db.command("listCollections", filter={"name": "markers"})
            if coll_info['cursor']['firstBatch']:
                validator = coll_info['cursor']['firstBatch'][0].get('options', {}).get('validator')
                if validator:
                    print(f"     - Validation: ✅ Active (Lean-Deep 3.1)")
                else:
                    print(f"     - Validation: ❌ Not configured")
    
    # Test write permissions
    print("\n🔐 Testing write permissions...")
    test_collection = db['_test_permissions']
    test_doc = {"test": True, "timestamp": "test"}
    
    try:
        result = test_collection.insert_one(test_doc)
        test_collection.delete_one({"_id": result.inserted_id})
        print("   ✅ Write permissions confirmed")
    except Exception as e:
        print(f"   ❌ Write test failed: {e}")
    
    print("\n✨ Database connection test completed successfully!")
    
except Exception as e:
    print(f"\n❌ Connection failed: {e}")
    print("\nPossible issues:")
    print("- Check your internet connection")
    print("- Verify your MongoDB Atlas password")
    print("- Ensure your IP is whitelisted in MongoDB Atlas")
    print("- Check if the connection string is properly formatted")
    sys.exit(1)
finally:
    if 'client' in locals():
        client.close()