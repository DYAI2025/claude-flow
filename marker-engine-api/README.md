# MarkerEngine Core API

Das zentrale Nervensystem der MarkerEngine zur Übersetzung von Sprache in strukturierte Marker.

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- MongoDB Atlas Account
- Docker (optional)

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd marker-engine-api
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env and replace <DEIN_PASSWORT_HIER_EINFÜGEN> with your MongoDB password
```

### 🔐 Database Setup

1. **Configure Database Connection:**
   ```bash
   # Edit .env file
   DATABASE_URL="mongodb+srv://benpoersch:<YOUR_PASSWORD>@markerengine.3ed5u3.mongodb.net/?retryWrites=true&w=majority&appName=MarkerEngine"
   ```
   
   ⚠️ **Security Note:** Never commit the `.env` file with your actual password to version control!

2. **Initialize Database:**
   ```bash
   # Run the initialization script to create collections, indexes, and validation
   python scripts/init_database.py
   ```
   
   This script will:
   - Create required collections: `markers`, `schemas`, `detectors`, `events`
   - Set up Lean-Deep 3.1 schema validation for the markers collection
   - Create performance indexes
   - Verify the setup with validation tests

3. **Import Markers (Optional):**
   ```bash
   # Import JSON marker files
   ./scripts/import_markers.sh "$DATABASE_URL" markers /path/to/json/files
   ```

### Running the Application

#### Local Development:
```bash
uvicorn app.main:app --reload
```

#### Docker:
```bash
docker-compose up --build
```

The API will be available at http://localhost:8000

## 📚 API Documentation

Interactive API documentation is available at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 🔍 Endpoints

### Health Check
- `GET /healthz` - Check API and database connectivity

### Markers
- `POST /markers` - Create a new marker
- `GET /markers` - List all markers (with pagination)
- `GET /markers/{marker_id}` - Get a specific marker

### Analysis
- `POST /analyze` - Analyze text and detect markers

## 🧪 Testing

Run tests with coverage:
```bash
pytest
```

View coverage report:
```bash
open htmlcov/index.html
```

## 🏗️ Project Structure

```
marker-engine-api/
├── app/
│   ├── models/         # Pydantic models
│   ├── routes/         # API endpoints
│   ├── services/       # Business logic
│   ├── config.py       # Configuration
│   ├── database.py     # Database connection
│   └── main.py         # FastAPI application
├── tests/              # Test suite
├── scripts/            # Utility scripts
│   ├── init_database.py    # Database initialization
│   └── import_markers.sh   # Marker import utility
├── requirements.txt    # Python dependencies
├── Dockerfile          # Container configuration
├── docker-compose.yml  # Docker Compose setup
├── .env.example        # Environment template
└── README.md           # This file
```

## 🔧 Configuration

Key environment variables:
- `DATABASE_URL` - MongoDB Atlas connection string (required)
- `MONGO_DB_NAME` - Database name (default: marker_engine)
- `API_HOST` - API host (default: 0.0.0.0)
- `API_PORT` - API port (default: 8000)
- `DETECTOR_PATH` - Path to detector scripts

## 📊 Lean-Deep 3.1 Compliance

All markers follow the Lean-Deep 3.1 specification:
- Required fields: `_id`, `frame`, `examples`
- XOR constraint: `pattern` OR `composed_of` OR `detect_class` (only one allowed)
- Minimum 5 examples per marker
- Structured activation and scoring rules

The database enforces these constraints through MongoDB schema validation.

## 🛡️ Security Best Practices

1. **Never commit `.env` files** with real passwords
2. **Use environment variables** for all sensitive configuration
3. **Validate all inputs** before database operations
4. **Use connection string** with proper authentication
5. **Enable SSL/TLS** for production deployments

## 🚨 Troubleshooting

### Database Connection Issues
- Ensure your IP is whitelisted in MongoDB Atlas
- Verify the password doesn't contain special characters that need URL encoding
- Check that the connection string is properly formatted

### Validation Errors
- Markers must conform to Lean-Deep 3.1 schema
- Use `scripts/init_database.py` to verify validation is active
- Check logs for detailed validation error messages