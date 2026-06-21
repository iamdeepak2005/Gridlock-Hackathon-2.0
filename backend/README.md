# 🔱 TRINETRA AI — Backend (FastAPI + ML Engine)

> Event-Driven Traffic Intelligence System — Backend API & ML Pipeline

---

## 📋 Table of Contents

- [Architecture](#-architecture)
- [Tech Stack](#-tech-stack)
- [Features](#-features)
- [ML Pipeline & Algorithms](#-ml-pipeline--algorithms)
- [API Endpoints](#-api-endpoints)
- [Setup & Installation](#-setup--installation)
- [Database](#-database)
- [Environment Variables](#-environment-variables)
- [Running Tests](#-running-tests)
- [Docker](#-docker)

---

## 🏗️ Architecture

The backend follows a **Clean Architecture** pattern:

```
backend/
├── app/
│   ├── api/                  # FastAPI route handlers (controllers)
│   │   ├── router.py         # Root router aggregating all endpoints
│   │   ├── impact.py         # POST /predict-impact
│   │   ├── resources.py      # POST /recommend-resources
│   │   ├── similar.py        # POST /similar-events
│   │   ├── resolution.py     # POST /predict-resolution
│   │   ├── feedback.py       # POST /feedback, GET /model-performance
│   │   ├── diversion.py      # POST /simulate-diversion
│   │   ├── events.py         # GET /events (from database)
│   │   ├── copilot.py        # POST /copilot (Gemini AI)
│   │   └── health.py         # GET /health
│   │
│   ├── services/             # Business logic layer
│   │   ├── impact_service.py
│   │   ├── resource_service.py
│   │   ├── similarity_service.py
│   │   ├── resolution_service.py
│   │   ├── feedback_service.py
│   │   ├── diversion_service.py
│   │   └── copilot_service.py   # Gemini API integration
│   │
│   ├── ml/                   # Machine Learning models
│   │   ├── impact_model.py        # Impact scoring (0-100)
│   │   ├── resolution_model.py    # Resolution time prediction
│   │   ├── resource_model.py      # Resource recommendation (K-Means)
│   │   ├── similarity_model.py    # Similar event retrieval (KNN)
│   │   ├── feature_engineering.py # Shared feature pipeline
│   │   ├── model_registry.py      # Model save/load/track
│   │   └── data_inspector.py      # Data quality inspection
│   │
│   ├── models/               # Data models
│   │   ├── database.py       # SQLAlchemy ORM models
│   │   └── schemas.py        # Pydantic request/response schemas
│   │
│   ├── repositories/         # Data access layer
│   │   ├── event_repository.py
│   │   └── prediction_log_repository.py
│   │
│   ├── simulation/           # Traffic simulation engine
│   │   └── traffic_diversion.py   # OSMnx + NetworkX simulation
│   │
│   ├── training/             # ML training pipeline
│   │   └── train_all.py      # End-to-end training orchestrator
│   │
│   ├── database/             # Database management
│   │   ├── connection.py     # SQLAlchemy engine & session
│   │   └── seed.py           # CSV → database seeder
│   │
│   ├── utils/                # Shared utilities
│   │   └── helpers.py        # Constants, severity maps
│   │
│   ├── config.py             # Pydantic Settings (env vars)
│   └── main.py               # FastAPI application entry point
│
├── tests/                    # Pytest test suite
├── trained_models/           # Serialized ML models (.joblib)
├── data/                     # Dataset CSV files
├── osmnx_cache/              # Cached road network graphs
├── requirements.txt          # Python dependencies
├── Dockerfile                # Docker image definition
└── .env.example              # Environment variable template
```

---

## 🛠️ Tech Stack

| Category | Technology |
|---|---|
| **Framework** | FastAPI 0.115 |
| **Language** | Python 3.12 |
| **Database** | PostgreSQL 16 (production) / SQLite (dev) |
| **ORM** | SQLAlchemy 2.0 |
| **ML Libraries** | scikit-learn, XGBoost, LightGBM, CatBoost |
| **Geospatial** | OSMnx, NetworkX, GeoPandas |
| **AI Copilot** | Google Gemini 2.5 Flash API |
| **Validation** | Pydantic v2 |
| **Testing** | Pytest + httpx |
| **Serialization** | joblib |

---

## ✨ Features

### 1. 🎯 Impact Scoring Engine
Predicts event severity on a 0-100 scale using a composite impact score derived from:
- Event cause severity (25 pts)
- Road closure status (20 pts)
- Priority level (15 pts)
- Resolution time percentile (15 pts)
- Corridor importance (10 pts)
- Peak hour bonus (10 pts)
- Vehicle involvement (5 pts)

### 2. 🚔 Resource Recommendation Engine
Recommends officers, barricades, and tow vehicles using:
- K-Means clustering of historical incidents
- Domain-specific rule-based inference per event cause
- Cluster profiles blended with rules for hybrid recommendations

### 3. 🔍 Similar Event Retrieval
Finds historically similar incidents using multi-modal embeddings:
- Categorical features (OneHot encoding)
- Text features (TF-IDF on descriptions)
- Geospatial features (scaled lat/lng)
- Binary features (road closure)
- NearestNeighbors with cosine similarity

### 4. ⏱️ Resolution Time Prediction
Predicts how long an event will take to resolve (in minutes):
- Log-transforms the target for better distribution
- Uses `closed_datetime - start_datetime` as ground truth
- Caps at 7 days (10,080 minutes)

### 5. 🗺️ Traffic Diversion Simulation
Real-time traffic diversion computation:
- Downloads road graphs from OpenStreetMap via OSMnx
- Identifies blocked edges within impact radius
- Computes alternative routes using NetworkX shortest path
- Calculates congestion risk score using edge betweenness centrality
- Caches road graphs to disk for fast subsequent lookups
- Falls back to synthetic simulation when OSMnx is unavailable

### 6. 🤖 AI Traffic Copilot
Natural language operator interface powered by Google Gemini:
- Processes operator queries in natural language
- Auto-extracts structured event data from incident reports
- Provides tactical responses with recommended actions
- Outputs `[EVENT_JSON]` for automatic event creation

### 7. 📊 Feedback & Continual Learning
- Logs every prediction with input/output for audit
- Accepts operator feedback on prediction accuracy
- Computes drift scores between predicted and actual outcomes
- Tracks model performance metrics over time

---

## 🧠 ML Pipeline & Algorithms

### Training Pipeline

The training pipeline (`python -m app.training.train_all <csv_path>`) executes:

```
Step 1: Load CSV dataset (8,173 traffic events from Bengaluru)
   ↓
Step 2: Data Quality Inspection
   • Detect missing values, duplicates, outliers
   • Auto-clean: fill nulls, remove invalid rows
   ↓
Step 3: Feature Engineering
   • Encode categoricals (event_type, event_cause, zone, junction, corridor)
   • Extract temporal features (hour, day_of_week, is_peak_hour)
   • Binary features (requires_road_closure, has_vehicle)
   • Priority encoding
   ↓
Step 4: Train Impact Model (4 algorithms)
Step 5: Train Resolution Model (4 algorithms)
Step 6: Train Resource Model (K-Means clustering)
Step 7: Build Similarity Index (TF-IDF + KNN)
   ↓
Step 8: Auto-select best model per feature → Save to ./trained_models/
```

### Algorithms & Model Selection

| Feature | Algorithms Trained | Selection Metric | Selection Method |
|---|---|---|---|
| **Impact Score** | XGBoost, LightGBM, CatBoost, Random Forest | Best R² score | GridSearchCV (3-fold CV) |
| **Resolution Time** | XGBoost, LightGBM, CatBoost, Random Forest | Best R² score | GridSearchCV (3-fold CV) |
| **Resources** | K-Means Clustering + Rule-based | Silhouette score | Sweep k=4..9, pick best |
| **Similar Events** | TF-IDF + OneHotEncoder + NearestNeighbors | Cosine similarity | Brute-force KNN |

### Feature Engineering Details

The `FeatureEngineer` class performs:
1. **Categorical Encoding**: One-hot encoding for `event_type`, `event_cause`, `zone`, `junction`, `corridor`, `veh_type`
2. **Temporal Features**: Extracts `hour`, `day_of_week`, `month`, `is_weekend`, `is_peak_hour` from `start_datetime`
3. **Binary Features**: `requires_road_closure`, `has_vehicle_info`
4. **Priority Encoding**: Maps `High → 1`, `Low → 0`
5. **Handles unknown categories** at inference time gracefully

### Hyperparameter Tuning

Each model is tuned via `GridSearchCV` with:
- **XGBoost/LightGBM**: `n_estimators ∈ {100, 200}`, `max_depth ∈ {4, 6, 8}`, `learning_rate ∈ {0.05, 0.1}`
- **CatBoost**: `iterations ∈ {100, 200}`, `depth ∈ {4, 6}`, `learning_rate ∈ {0.05, 0.1}`
- **Random Forest**: `n_estimators ∈ {100, 200}`, `max_depth ∈ {6, 10, 15}`
- **K-Means**: `n_clusters ∈ {4, 5, 6, 7, 8, 9}`

---

## 📡 API Endpoints

All endpoints are available under `/api/v1/` prefix and at root level.

| Endpoint | Method | Description | Request Body |
|---|---|---|---|
| `/predict-impact` | POST | Predict event impact score (0-100) | `ImpactPredictionRequest` |
| `/recommend-resources` | POST | Recommend officers, barricades, tow vehicles | `ResourceRecommendationRequest` |
| `/similar-events` | POST | Find similar historical events | `SimilarEventRequest` |
| `/predict-resolution` | POST | Predict resolution time (minutes) | `ResolutionPredictionRequest` |
| `/feedback` | POST | Submit prediction feedback | `FeedbackRequest` |
| `/model-performance` | GET | Get model metrics & drift scores | — |
| `/simulate-diversion` | POST | Simulate traffic diversion routes | `DiversionRequest` |
| `/events` | GET | Fetch events from database | Query: `limit`, `offset` |
| `/copilot` | POST | AI Copilot natural language query | `CopilotRequest` |
| `/health` | GET | System health check | — |

### Interactive API Docs

Once running, visit:
- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## 🚀 Setup & Installation

### Prerequisites
- Python 3.12+
- PostgreSQL 16+ (or use SQLite for local dev)

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your values (especially GEMINI_API_KEY)
```

### 3. Train ML Models

```bash
python -m app.training.train_all data/events.csv
```

This will:
- Inspect data quality automatically
- Engineer features from raw data
- Train 4 algorithms per feature (Impact, Resolution)
- Train K-Means clustering for Resource recommendations
- Build TF-IDF + KNN similarity index
- Auto-select best model per feature
- Save all models to `./trained_models/`

### 4. Seed Database (Optional)

```bash
python -m app.database.seed data/events.csv
```

### 5. Start Server

```bash
uvicorn app.main:app --reload --port 8000
```

### 6. Open API Docs

Visit [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 🗄️ Database

### Schema

The database has 3 tables:

| Table | Purpose |
|---|---|
| `traffic_events` | Full traffic event dataset (8,173 records) |
| `prediction_logs` | Logs every prediction for continual learning |
| `model_metadata` | Model registry tracking trained models & metrics |

### Connection

- **Production**: PostgreSQL via `DATABASE_URL=postgresql://trinetra:trinetra_pass@postgres:5432/trinetra_db`
- **Development**: SQLite via `DATABASE_URL=sqlite:///./trinetra.db`

The backend auto-detects the database type and configures the engine accordingly (SQLite uses `check_same_thread=False`, PostgreSQL uses connection pooling).

---

## 🔐 Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `DATABASE_URL` | Yes | `postgresql://...` | Database connection string |
| `APP_ENV` | No | `development` | Environment name |
| `APP_DEBUG` | No | `true` | Enable debug mode |
| `MODEL_DIR` | No | `./trained_models` | Path to trained model files |
| `DATA_PATH` | No | `./data/events.csv` | Path to training dataset |
| `OSMNX_CACHE_DIR` | No | `./osmnx_cache` | Cache dir for road graphs |
| `GEMINI_API_KEY` | Yes* | `None` | Google Gemini API key (*required for Copilot) |

---

## 🧪 Running Tests

```bash
cd backend
pytest tests/ -v
```

Test coverage includes:
- Impact prediction endpoint
- Resource recommendation endpoint
- Similar events retrieval
- Resolution time prediction
- Feedback submission
- Traffic diversion simulation
- AI Copilot endpoint

---

## 🐳 Docker

### Build & Run (Standalone)

```bash
cd backend
docker build -t trinetra-backend .
docker run -p 8000:8000 \
  -e DATABASE_URL=sqlite:///./trinetra.db \
  -e GEMINI_API_KEY=your_key_here \
  trinetra-backend
```

### With Docker Compose (Recommended)

See the root-level `docker-compose.yml` for full-stack orchestration with PostgreSQL and the frontend.

```bash
# From project root
docker-compose up --build
```

### Train Models Inside Container

```bash
docker-compose exec backend python -m app.training.train_all /app/data/events.csv
```

### Seed Database Inside Container

```bash
docker-compose exec backend python -m app.database.seed /app/data/events.csv
```

---

## 📊 Dataset

- **8,173** anonymized traffic events from Bengaluru
- **17** event causes: `vehicle_breakdown`, `accident`, `tree_fall`, `water_logging`, `congestion`, `construction`, `pot_holes`, `road_conditions`, `protest`, `procession`, `vip_movement`, `public_event`, `debris`, `fog/low_visibility`, `test_demo`, `others`
- **10** traffic zones, **294** junctions, **22** corridors
- Date range: November 2023 — 2024
- Fields include: geolocation, timestamps, priority, status, vehicle info, road closure status, descriptions, resolution times

---

## 📜 License

Hackathon project — **TRINETRA AI** | Gridlock Hackathon 2.0
