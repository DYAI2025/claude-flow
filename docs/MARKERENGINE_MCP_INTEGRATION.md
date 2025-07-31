# MarkerEngine MCP Integration Guide

This guide explains how to set up and use the MarkerEngine with MongoDB through the Claude Flow MCP server.

## Prerequisites

1. MongoDB Atlas account with a cluster named `markerengine`
2. Python 3.11+ for MarkerEngine API
3. Node.js 18+ for Claude Flow MCP server
4. Claude Code with MCP support

## Setup Instructions

### 1. Configure MongoDB Connection

Create a `.env` file in the `marker-engine-api` directory:

```bash
cd marker-engine-api
cp .env.example .env
```

Edit the `.env` file and replace `<YOUR_PASSWORD>` with your MongoDB password:

```env
DATABASE_URL="mongodb+srv://benpoersch:<YOUR_PASSWORD>@markerengine.3ed5u3.mongodb.net/?retryWrites=true&w=majority&appName=MarkerEngine"
```

### 2. Initialize the Database

Run the initialization script to set up collections and validation:

```bash
cd marker-engine-api
python scripts/init_database.py
```

This will:
- Create required collections: `markers`, `schemas`, `detectors`, `events`
- Set up Lean-Deep 3.1 schema validation
- Create performance indexes
- Verify the setup

### 3. Start the MarkerEngine API

#### Option A: Using Python directly
```bash
cd marker-engine-api
pip install -r requirements.txt
uvicorn app.main:app --reload
```

#### Option B: Using Docker
```bash
cd marker-engine-api
docker-compose up --build
```

The API will be available at http://localhost:8000

### 4. Configure Claude Flow MCP Server

The MCP server already includes MarkerEngine tools. Start it with:

```bash
npx claude-flow mcp start --stdio
```

## Available MCP Tools

### Marker Management
- `marker_create` - Create a new marker in the database
- `marker_get` - Retrieve a specific marker by ID
- `marker_list` - List all markers with pagination
- `marker_search` - Search markers by concept, tags, or pattern
- `marker_analyze` - Analyze text and detect markers

### Database Management
- `markerdb_status` - Check database connection and stats
- `markerdb_init` - Initialize database with schema validation
- `markerdb_import` - Import markers from JSON files
- `markerdb_export` - Export markers to JSON format

## Usage Examples

### Create a Marker
```javascript
mcp__claude-flow__marker_create({
  id: "A_EXAMPLE_MARKER",
  frame: {
    signal: ["example", "test"],
    concept: "Testing",
    pragmatics: "Used for testing",
    narrative: "This is a test marker"
  },
  examples: [
    "This is an example",
    "Another example here",
    "Testing example three"
  ],
  pattern: ["example.*test"]
})
```

### Search Markers
```javascript
mcp__claude-flow__marker_search({
  query: "emotion",
  field: "concept",
  limit: 20
})
```

### Analyze Text
```javascript
mcp__claude-flow__marker_analyze({
  text: "I feel really happy today!",
  mode: "deep"
})
```

## API Endpoints

The MarkerEngine API provides these endpoints:

- `GET /healthz` - Health check
- `POST /markers` - Create marker
- `GET /markers` - List markers
- `GET /markers/{marker_id}` - Get specific marker
- `POST /analyze` - Analyze text

Full API documentation: http://localhost:8000/docs

## Troubleshooting

### MongoDB Connection Issues
1. Ensure your IP is whitelisted in MongoDB Atlas
2. Check password doesn't contain special characters needing encoding
3. Verify cluster name is correct

### MCP Server Issues
1. Ensure Claude Flow is installed: `npm install -g claude-flow@alpha`
2. Check MCP server is running: `npx claude-flow mcp status`
3. Verify tools are loaded: `npx claude-flow mcp tools`

### Database Validation Errors
1. Markers must follow Lean-Deep 3.1 schema
2. Required fields: `_id`, `frame`, `examples`
3. XOR constraint: only one of `pattern`, `composed_of`, or `detect_class`

## Architecture

```
Claude Code
    ↓
MCP Protocol (stdio)
    ↓
Claude Flow MCP Server
    ↓
MarkerEngine Tools
    ↓
MarkerEngine API (FastAPI)
    ↓
MongoDB Atlas
```

## Security Notes

1. Never commit `.env` files with passwords
2. Use environment variables for sensitive data
3. Enable MongoDB Atlas IP whitelisting
4. Use connection strings with SSL/TLS
5. Rotate API keys regularly