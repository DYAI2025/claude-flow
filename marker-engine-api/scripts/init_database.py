#!/usr/bin/env python3
"""
Database Initialization Script for MarkerEngine
Creates collections, sets up validation schemas, and creates indexes
"""

import asyncio
import os
import sys
from pathlib import Path
from pymongo import MongoClient
from pymongo.errors import CollectionInvalid, OperationFailure
import logging
from dotenv import load_dotenv

# Add parent directory to path to import app modules
sys.path.append(str(Path(__file__).parent.parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Get database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "marker_engine")

if not DATABASE_URL:
    logger.error("DATABASE_URL environment variable is not set!")
    sys.exit(1)

if "<" in DATABASE_URL or ">" in DATABASE_URL:
    logger.error("DATABASE_URL still contains placeholder password!")
    sys.exit(1)

# Lean-Deep 3.1 Schema Validation for markers collection
MARKER_VALIDATION_SCHEMA = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": ["_id", "frame", "examples"],
        "properties": {
            "_id": {
                "bsonType": "string",
                "description": "Unique marker identifier"
            },
            "frame": {
                "bsonType": "object",
                "required": ["signal", "concept", "pragmatics", "narrative"],
                "properties": {
                    "signal": {
                        "oneOf": [
                            {"bsonType": "string"},
                            {"bsonType": "array", "items": {"bsonType": "string"}}
                        ]
                    },
                    "concept": {"bsonType": "string"},
                    "pragmatics": {"bsonType": "string"},
                    "narrative": {"bsonType": "string"}
                }
            },
            "examples": {
                "bsonType": "array",
                "minItems": 1,
                "items": {"bsonType": "string"}
            },
            "pattern": {
                "oneOf": [
                    {"bsonType": "string"},
                    {"bsonType": "array", "items": {"bsonType": "string"}},
                    {"bsonType": "null"}
                ]
            },
            "composed_of": {
                "oneOf": [
                    {"bsonType": "array", "items": {"bsonType": "string"}},
                    {"bsonType": "null"}
                ]
            },
            "detect_class": {
                "oneOf": [
                    {"bsonType": "string"},
                    {"bsonType": "null"}
                ]
            },
            "activation": {
                "oneOf": [
                    {"bsonType": "object"},
                    {"bsonType": "null"}
                ]
            },
            "scoring": {
                "oneOf": [
                    {"bsonType": "object"},
                    {"bsonType": "null"}
                ]
            },
            "tags": {
                "oneOf": [
                    {"bsonType": "array", "items": {"bsonType": "string"}},
                    {"bsonType": "null"}
                ]
            }
        },
        # Ensure XOR constraint: only one of pattern, composed_of, or detect_class
        "oneOf": [
            {
                "required": ["pattern"],
                "properties": {
                    "composed_of": {"bsonType": "null"},
                    "detect_class": {"bsonType": "null"}
                }
            },
            {
                "required": ["composed_of"],
                "properties": {
                    "pattern": {"bsonType": "null"},
                    "detect_class": {"bsonType": "null"}
                }
            },
            {
                "required": ["detect_class"],
                "properties": {
                    "pattern": {"bsonType": "null"},
                    "composed_of": {"bsonType": "null"}
                }
            }
        ]
    }
}

def init_database():
    """Initialize MongoDB collections, validation, and indexes"""
    
    try:
        # Connect to MongoDB
        logger.info(f"Connecting to MongoDB...")
        client = MongoClient(DATABASE_URL)
        db = client[MONGO_DB_NAME]
        
        # Test connection
        client.server_info()
        logger.info(f"Successfully connected to MongoDB database: {MONGO_DB_NAME}")
        
        # Collections to create
        collections = {
            "markers": {
                "validator": MARKER_VALIDATION_SCHEMA,
                "indexes": [
                    ("level", 1),
                    ("composed_of", 1),
                    ("tags", 1),
                    ("frame.concept", 1)
                ]
            },
            "schemas": {
                "indexes": [
                    ("name", 1),
                    ("version", 1)
                ]
            },
            "detectors": {
                "indexes": [
                    ("name", 1),
                    ("fires_marker", 1),
                    ("active", 1)
                ]
            },
            "events": {
                "indexes": [
                    [("conversation_id", 1), ("ts", -1)],
                    ("marker_id", 1),
                    ("ts", -1)
                ]
            }
        }
        
        # Create collections with validation
        for collection_name, config in collections.items():
            logger.info(f"\nProcessing collection: {collection_name}")
            
            # Check if collection exists
            if collection_name in db.list_collection_names():
                logger.info(f"  Collection '{collection_name}' already exists")
                
                # Update validation if specified
                if "validator" in config:
                    try:
                        db.command("collMod", collection_name, validator=config["validator"])
                        logger.info(f"  ✓ Updated validation schema for '{collection_name}'")
                    except OperationFailure as e:
                        logger.warning(f"  ⚠ Could not update validation: {e}")
            else:
                # Create collection with validation
                try:
                    if "validator" in config:
                        db.create_collection(collection_name, validator=config["validator"])
                        logger.info(f"  ✓ Created collection '{collection_name}' with validation")
                    else:
                        db.create_collection(collection_name)
                        logger.info(f"  ✓ Created collection '{collection_name}'")
                except CollectionInvalid:
                    logger.info(f"  Collection '{collection_name}' already exists")
            
            # Create indexes
            if "indexes" in config:
                collection = db[collection_name]
                for index_spec in config["indexes"]:
                    try:
                        if isinstance(index_spec, list):
                            # Compound index
                            index_name = collection.create_index(index_spec)
                        else:
                            # Single field index
                            index_name = collection.create_index(index_spec)
                        logger.info(f"  ✓ Created index: {index_spec}")
                    except Exception as e:
                        logger.warning(f"  ⚠ Index may already exist: {index_spec}")
        
        # Verify setup
        logger.info("\n" + "="*50)
        logger.info("Database initialization completed successfully!")
        logger.info("="*50)
        
        # Show collection stats
        logger.info("\nCollection Summary:")
        for collection_name in db.list_collection_names():
            count = db[collection_name].count_documents({})
            logger.info(f"  - {collection_name}: {count} documents")
        
        # Test marker validation
        logger.info("\nTesting marker validation...")
        test_valid_marker = {
            "_id": "TEST_VALIDATION_MARKER",
            "frame": {
                "signal": ["test signal"],
                "concept": "test",
                "pragmatics": "testing",
                "narrative": "validation"
            },
            "examples": ["Test example"],
            "pattern": ["test pattern"]
        }
        
        try:
            # Try to insert and then remove test marker
            db.markers.insert_one(test_valid_marker)
            db.markers.delete_one({"_id": "TEST_VALIDATION_MARKER"})
            logger.info("  ✓ Validation test passed - Lean-Deep 3.1 schema is active")
        except Exception as e:
            logger.error(f"  ✗ Validation test failed: {e}")
        
        # Test invalid marker (should fail)
        test_invalid_marker = {
            "_id": "TEST_INVALID",
            "frame": {"concept": "test"},  # Missing required fields
            "examples": []  # Empty array not allowed
        }
        
        try:
            db.markers.insert_one(test_invalid_marker)
            db.markers.delete_one({"_id": "TEST_INVALID"})
            logger.warning("  ⚠ Invalid marker was accepted - validation may not be working")
        except Exception:
            logger.info("  ✓ Invalid marker rejected - validation is working correctly")
        
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        sys.exit(1)
    finally:
        if 'client' in locals():
            client.close()

if __name__ == "__main__":
    logger.info("MarkerEngine Database Initialization")
    logger.info("=" * 50)
    init_database()