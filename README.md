# Car Marketplace Aggregator

An Estonian car marketplace aggregator that scrapes listings from multiple sources (Auto24, AutoDiiler, Veego), normalises them into a unified taxonomy, and serves them through a FastAPI backend with a Next.js frontend.

---

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Environment Variables](#environment-variables)
  - [Running with Docker Compose](#running-with-docker-compose)
- [Docker Compose Profiles](#docker-compose-profiles)
- [How It Works](#how-it-works)
  - [Taxonomy & Seeding](#taxonomy--seeding)
  - [Scraping Pipeline](#scraping-pipeline)
  - [API](#api)
- [API Endpoints](#api-endpoints)
- [Environment Variable Reference](#environment-variable-reference)

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        Docker Compose                           │
│                                                                 │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌─────────────┐  │
│  │ MongoDB  │◄──│   API    │   │   Cron   │   │  Scrapers   │  │
│  │  (data)  │◄──│ (FastAPI │   │(scheduled│   │ (one-shot)  │  │
│  │          │◄──│ + Next.js│   │ scraping)│   │             │  │
│  │          │   │  static) │   │          │   │             │  │
│  └──────────┘   └──────────┘   └──────────┘   └─────────────┘  │
│       ▲                                                         │
│       │         ┌──────────┐   ┌─────────────┐                  │
│       └─────────│  Ngrok   │   │Mongo Express│                  │
│                 │ (tunnel) │   │  (DB admin) │                  │
│                 └──────────┘   └─────────────┘                  │
└─────────────────────────────────────────────────────────────────┘
```

The application consists of several services:

| Service           | Description                                                                 | Always runs? |
|-------------------|-----------------------------------------------------------------------------|--------------|
| **mongodb**       | MongoDB 7.0 database storing all listings and taxonomy data                 | ✅ Yes        |
| **api**           | FastAPI backend + statically exported Next.js frontend                      | ✅ Yes        |
| **cron**          | Scheduled scraper runs (configurable via `SCRAPER_CRON_SCHEDULE` env var)   | ✅ Yes        |
| **scrapers**      | One-shot scraper run (for manual/initial data population)                   | ❌ Profile    |
| **ngrok**         | Ngrok tunnel to expose the API publicly                                     | ❌ Profile    |
| **mongo-express** | Web-based MongoDB admin UI                                                  | ✅ Yes        |

---

## Tech Stack

**Backend:**
- Python 3.11, FastAPI, Uvicorn
- MongoDB (pymongo)
- Pydantic v2 + pydantic-settings
- aiohttp, curl_cffi (Cloudflare bypass), BeautifulSoup4

**Frontend:**
- Next.js 14 (static export), React 18, TypeScript
- Tailwind CSS
- Axios, Lucide React icons

**Infrastructure:**
- Docker & Docker Compose (multi-stage builds)
- Cron (scheduled scraping)
- Ngrok (optional tunnelling)

---

## Project Structure

```
├── compose.yaml              # Docker Compose orchestration
├── Dockerfile                 # Multi-stage build (frontend → base → api/scrapers/cron)
├── requirements.txt           # Python dependencies
├── backend/
│   ├── app/                   # FastAPI application (Clean Architecture)
│   │   ├── main.py            # App factory + lifespan
│   │   ├── config.py          # App configuration (pydantic-settings)
│   │   ├── domain/            # Business logic layer
│   │   │   ├── entities/      # Domain models (CarListing)
│   │   │   ├── dtos/          # Data transfer objects
│   │   │   ├── enums/         # Enumerations
│   │   │   ├── exceptions/    # Domain exceptions
│   │   │   ├── interfaces/    # Repository interfaces (ports)
│   │   │   └── use_cases/     # Application use cases
│   │   ├── infrastructure/    # External adapters
│   │   │   ├── database/      # MongoDB client & repository implementation
│   │   │   └── logging/       # Structured logging
│   │   └── presentation/      # HTTP layer
│   │       ├── dependencies.py
│   │       ├── middlewares/    # Error handling, request logging
│   │       └── routers/       # API route handlers
│   ├── cron/
│   │   └── scrapers.cron      # Cron schedule template (envsubst)
│   └── scrapers/              # Scraping engine
│       ├── main.py            # Scraper orchestrator
│       ├── config.py          # Scraper configuration
│       ├── repository.py      # Scraper-side MongoDB repository
│       ├── resolver.py        # Taxonomy resolver (source → canonical)
│       ├── mark_top_brands.py # Marks popular brands with is_top flag
│       ├── scrapers/          # Individual scraper implementations
│       │   ├── auto24_scraper.py
│       │   ├── autodiiler_scraper.py
│       │   ├── veego_scraper.py
│       │   └── ...
│       └── seeders/           # Taxonomy seeding scripts
│           ├── seed_auto24_catalog.py
│           ├── seed_autodiiler.py
│           ├── seed_veego.py
│           └── seed_source_taxonomy.py
└── frontend/                  # Next.js frontend
    ├── app/                   # App router (layout, page, styles)
    ├── components/            # React components
    └── types/                 # TypeScript type definitions
```

### Clean Architecture (Backend API)

The backend follows **Clean Architecture** principles:

```
Presentation (routers, middlewares)
       │
       ▼
   Use Cases (business operations)
       │
       ▼
    Domain (entities, interfaces, DTOs, exceptions)
       │
       ▼
Infrastructure (MongoDB repository, logging)
```

- **Domain layer** — pure business logic with no external dependencies. Defines entities (`CarListing`), repository interfaces (`ICarListingRepository`), DTOs, and custom exceptions.
- **Use Cases** — orchestrate domain logic: `GetListings`, `GetListingById`, `CompareCars`, `GetFilterOptions`, `GetStatistics`.
- **Infrastructure** — implements domain interfaces: `MongoCarListingRepository`, MongoDB client, structured logging.
- **Presentation** — FastAPI routers, dependency injection, error-handling middleware, request logging middleware.

---

## Getting Started

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) (v20+)
- [Docker Compose](https://docs.docker.com/compose/install/) (v2+)

### Environment Variables

Create the following `.env` files in the project root before starting:

#### `.env.api`

Used by the **API** service and **MongoDB**.

```env
# MongoDB connection (used by API service)
MONGODB_HOST=mongodb
MONGODB_PORT=27017
MONGODB_DATABASE_NAME=car_index

# Application settings
APP_NAME=Car Index
APP_VERSION=1.0.0
APP_DEBUG=false

# CORS origins (comma-separated)
APP_CORS_ORIGINS=["*"]

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=HUMAN
```

#### `.env.scrapers`

Used by the **scrapers** and **cron** services.

```env
# MongoDB connection (used by scrapers)
MONGODB_URI=mongodb://mongodb:27017/car_index
DATABASE_NAME=car_index
COLLECTION_NAME=car_listings

# Scraping behaviour
MAX_PAGES=              # Leave empty for no limit
REQUEST_DELAY=1         # Seconds between requests
REQUEST_TIMEOUT=30      # Request timeout in seconds
MAX_RETRIES=3
BATCH_SIZE=10           # Concurrent async batch size

# Logging
LOG_LEVEL=INFO

# Cron schedule (default: every 12 hours)
# Uses standard cron syntax: minute hour day month weekday
SCRAPER_CRON_SCHEDULE=0 */12 * * *
```

#### `.env.ngrok` *(optional — only needed with `tunnel` profile)*

```env
NGROK_AUTHTOKEN=your_ngrok_auth_token_here
```

#### `.env.mongo-express` *(optional — for Mongo Express admin UI)*

```env
ME_CONFIG_MONGODB_URL=mongodb://mongodb:27017/
ME_CONFIG_BASICAUTH=false
```

### Running with Docker Compose

#### 1. Start core services (API + MongoDB + Cron + Mongo Express)

```bash
docker compose up -d
```

This starts the essential services:
- **MongoDB** — database
- **API** — FastAPI backend serving the Next.js frontend on port `8000`
- **Cron** — scheduled scraper runs (every 12 hours by default)
- **Mongo Express** — database admin UI on port `8081`

On first startup, the **cron** service automatically runs initial taxonomy seeding (Auto24, AutoDiiler, Veego catalogues + top brand markers) before starting the cron daemon. This ensures the application has the taxonomy data it needs to function.

#### 2. Trigger an initial scrape (one-shot)

After the taxonomy has been seeded, run the scrapers once to populate listings:

```bash
docker compose --profile scrapers run --rm scrapers
```

#### 3. Access the application

| Service        | URL                          |
|----------------|------------------------------|
| Application    | http://localhost:8000         |
| API docs       | http://localhost:8000/docs    |
| Mongo Express  | http://localhost:8081         |
| Ngrok inspect  | http://localhost:4040 *(if tunnel profile active)* |

#### 4. Stop all services

```bash
docker compose down
```

To also remove stored data:

```bash
docker compose down -v
```

---

## Docker Compose Profiles

Profiles let you opt-in to additional services that aren't needed in every scenario.

| Profile      | Services included | How to activate                                             | Purpose                              |
|--------------|-------------------|-------------------------------------------------------------|--------------------------------------|
| *(default)*  | mongodb, api, cron, mongo-express | `docker compose up -d`                       | Core application stack               |
| `scrapers`   | scrapers          | `docker compose --profile scrapers run --rm scrapers`       | One-shot scraper run                 |
| `tunnel`     | ngrok             | `docker compose --profile tunnel up -d`                     | Expose API publicly via Ngrok tunnel |

You can combine profiles:

```bash
docker compose --profile scrapers --profile tunnel up -d
```

---

## How It Works

### Taxonomy & Seeding

Before scraping can work correctly, the system needs a **canonical taxonomy** of car makes, series, and models. This is built by the seeding process:

1. **Auto24 catalogue** — scraped from Auto24's website; serves as the primary canonical source for makes/series/models.
2. **AutoDiiler catalogue** — scraped from AutoDiiler's API; creates taxonomy mappings so AutoDiiler listing data maps to canonical entities.
3. **Veego catalogue** — scraped from Veego's API; creates taxonomy mappings for Veego listings (includes Estonian translation layer).
4. **Top brands marker** — flags well-known brands (Toyota, BMW, etc.) with `is_top: true` for UI prioritisation.

Seeding runs automatically on first startup of the **cron** container (via an entrypoint script that checks if taxonomy data already exists). It can also be triggered manually:

```bash
docker compose --profile scrapers run --rm scrapers python -m scrapers.seeders.seed_auto24_catalog
```

### Scraping Pipeline

1. Scrapers fetch listings concurrently from multiple sources using async HTTP clients.
2. Each listing is normalised and upserted by `source_url` (deduplication).
3. A taxonomy **resolver** maps source-specific make/model labels to canonical IDs using `taxonomy_mappings`.
4. Stale listings (not seen in the current run) are automatically deleted per source.
5. The cron service repeats this process on a configurable schedule.

### API

The FastAPI application serves:
- **REST API** under `/api/` — listings, filtering, comparison, statistics
- **Static frontend** — the pre-built Next.js app at the root URL
- **Health check** at `/health`

---

## API Endpoints

| Method | Endpoint                                    | Description                         |
|--------|---------------------------------------------|-------------------------------------|
| GET    | `/health`                                   | Health check                        |
| GET    | `/api`                                      | API info                            |
| GET    | `/api/listings/`                            | List/search/filter listings         |
| GET    | `/api/listings/{id}`                        | Get listing by ID                   |
| GET    | `/api/listings/stats/overview`              | Listing statistics                  |
| GET    | `/api/listings/filter-options/makes`        | Available makes                     |
| GET    | `/api/listings/filter-options/series/{id}`  | Series for a make                   |
| GET    | `/api/listings/filter-options/models/{id}`  | Models for a make (optional series) |
| GET    | `/api/listings/filter-options/fuel-types`   | Available fuel types                |
| GET    | `/api/listings/filter-options/body-types`   | Available body types                |
| GET    | `/api/comparison/compare`                   | Compare cars by make/model/year     |
| GET    | `/api/comparison/similar/{id}`              | Find similar listings               |

---

## Environment Variable Reference

### API Service (`.env.api`)

| Variable               | Default         | Description                                      |
|------------------------|-----------------|--------------------------------------------------|
| `MONGODB_HOST`         | `localhost`     | MongoDB hostname                                 |
| `MONGODB_PORT`         | `27017`         | MongoDB port                                     |
| `MONGODB_DATABASE_NAME`| `car_index`     | Database name                                    |
| `MONGODB_USERNAME`     | *(none)*        | MongoDB username (optional)                      |
| `MONGODB_PASSWORD`     | *(none)*        | MongoDB password (optional)                      |
| `APP_NAME`             | `Car Index`     | Application display name                         |
| `APP_VERSION`          | `1.0.0`         | Application version string                       |
| `APP_DEBUG`            | `false`         | Enable debug mode                                |
| `APP_HOST`             | `0.0.0.0`       | Server bind host                                 |
| `APP_PORT`             | `8000`          | Server bind port                                 |
| `APP_CORS_ORIGINS`     | `["*"]`         | Allowed CORS origins (JSON array)                |
| `LOG_LEVEL`            | `INFO`          | Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)|
| `LOG_FORMAT`           | `HUMAN`         | Log format (HUMAN or JSON)                       |

### Scrapers & Cron (`.env.scrapers`)

| Variable                | Default                              | Description                                      |
|-------------------------|--------------------------------------|--------------------------------------------------|
| `MONGODB_URI`           | `mongodb://localhost:27017/car_index` | Full MongoDB connection URI                      |
| `DATABASE_NAME`         | `car_index`                          | Database name                                    |
| `COLLECTION_NAME`       | `car_listings`                       | Listings collection name                         |
| `MAX_PAGES`             | *(unlimited)*                        | Max pages to scrape per source                   |
| `REQUEST_DELAY`         | `1`                                  | Delay between requests (seconds)                 |
| `REQUEST_TIMEOUT`       | `30`                                 | HTTP request timeout (seconds)                   |
| `MAX_RETRIES`           | `3`                                  | Max retry attempts per request                   |
| `BATCH_SIZE`            | `10`                                 | Concurrent async batch size                      |
| `LOG_LEVEL`             | `INFO`                               | Log level                                        |
| `SCRAPER_CRON_SCHEDULE` | `0 */12 * * *`                       | Cron schedule for automated scraping             |

### Ngrok (`.env.ngrok`)

| Variable          | Default  | Description                |
|-------------------|----------|----------------------------|
| `NGROK_AUTHTOKEN` | *(none)* | Ngrok authentication token |

### Mongo Express (`.env.mongo-express`)

| Variable               | Default | Description                    |
|------------------------|---------|--------------------------------|
| `ME_CONFIG_MONGODB_URL`| *(none)*| MongoDB connection URL         |
| `ME_CONFIG_BASICAUTH`  | `true`  | Enable basic auth for web UI   |
