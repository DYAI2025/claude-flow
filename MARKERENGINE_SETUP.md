# MarkerEngine MongoDB Setup Instructions

## Quick Setup Guide

### 1. Add MongoDB Password

Edit the `.env` file in `marker-engine-api/`:

```bash
cd marker-engine-api
```

Open `.env` and replace `<YOUR_PASSWORD>` with your actual MongoDB password.

### 2. Test MongoDB Connection

Run the test script to verify connection:

```bash
cd ..
node scripts/test-markerengine-connection.js
```

### 3. Initialize Database

If connection is successful, initialize the database:

```bash
cd marker-engine-api
python scripts/init_database.py
```

### 4. Start MarkerEngine API

```bash
# In marker-engine-api directory
uvicorn app.main:app --reload
```

The API will be available at http://localhost:8000

### 5. Start MCP Server

In a new terminal:

```bash
npx claude-flow mcp start --stdio
```

## Available MCP Tools

The following MarkerEngine tools are now available in Claude Code:

- `mcp__claude-flow__marker_create` - Create a new marker
- `mcp__claude-flow__marker_get` - Get marker by ID
- `mcp__claude-flow__marker_list` - List all markers
- `mcp__claude-flow__marker_search` - Search markers
- `mcp__claude-flow__marker_analyze` - Analyze text for markers
- `mcp__claude-flow__markerdb_status` - Check database status
- `mcp__claude-flow__markerdb_init` - Initialize database
- `mcp__claude-flow__markerdb_import` - Import markers from JSON
- `mcp__claude-flow__markerdb_export` - Export markers to JSON

## Testing the Integration

1. Check database status:
```javascript
mcp__claude-flow__markerdb_status({ verbose: true })
```

2. Create a test marker:
```javascript
mcp__claude-flow__marker_create({
  id: "TEST_MARKER",
  frame: {
    signal: ["test"],
    concept: "Testing",
    pragmatics: "For testing purposes",
    narrative: "A test marker"
  },
  examples: ["This is a test"]
})
```

3. Search for markers:
```javascript
mcp__claude-flow__marker_search({
  query: "test",
  field: "concept"
})
```

## Troubleshooting

### MongoDB Connection Failed
- Check password is correct
- Ensure IP is whitelisted in MongoDB Atlas
- Verify cluster name is `markerengine`

### MCP Server Not Finding Tools
- Restart the MCP server
- Check for import errors in console
- Verify markerengine.js is in correct location

### API Not Responding
- Check MarkerEngine API is running on port 8000
- Verify no firewall blocking
- Check API logs for errors