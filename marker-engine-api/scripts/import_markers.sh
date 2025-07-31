#!/bin/bash

# Script to import JSON markers into MongoDB Atlas
# Usage: ./import_markers.sh <connection_string> <collection_name> <json_files_directory>

if [ "$#" -ne 3 ]; then
    echo "Usage: $0 <connection_string> <collection_name> <json_files_directory>"
    echo "Example: $0 'mongodb+srv://user:pass@cluster.mongodb.net/dbname' markers ./data"
    exit 1
fi

CONNECTION_STRING="$1"
COLLECTION="$2"
JSON_DIR="$3"

echo "Importing markers from $JSON_DIR to collection $COLLECTION..."

# Change to the directory containing JSON files
cd "$JSON_DIR" || exit 1

# Concatenate all JSON files and import
cat *.json | mongoimport --uri "$CONNECTION_STRING" --collection "$COLLECTION" --jsonArray

echo "Import completed!"