# Frontend-Backend Integration Guide

## Overview

The Estonian Car Marketplace Aggregator uses a **monolithic deployment** architecture where the FastAPI backend serves both the API endpoints and the static Next.js frontend files.

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                  FastAPI Server (Port 8000)         │
│                                                     │
│  ┌──────────────┐         ┌──────────────────────┐ │
│  │              │         │                      │ │
│  │   Next.js    │────────▶│   FastAPI Backend    │ │
│  │  Static SPA  │  AJAX   │   REST API           │ │
│  │              │         │   (/api/*)           │ │
│  │              │         │                      │ │
│  └──────────────┘         └──────────────────────┘ │
│       ▲                            │               │
│       │                            ▼               │
│   User Browser              MongoDB Database      │
└─────────────────────────────────────────────────────┘
```

## How It Works

### 1. Build Process

The application uses a multi-stage Docker build:

1. **Frontend Stage** (`frontend-builder`)
   - Builds the Next.js app with static export (`output: 'export'`)
   - Creates optimized static files in `frontend/out/`

2. **API Stage** (`api`)
   - Copies frontend static files to `/app/static/frontend`
   - Configures FastAPI to serve these files
   - Exposes port 8000

### 2. Request Routing

When the application runs:

#### Static File Requests
- Root path `/` → serves `index.html`
- Assets `/_next/*` → serves Next.js static assets
- Any other path (not starting with `/api` or `/health`) → serves `index.html` (SPA routing)

#### API Requests
- `/health` → Health check endpoint
- `/api/listings/*` → Listings API
- `/api/comparison/*` → Comparison API
- `/api` → API information

### 3. API Communication

The frontend makes API calls using relative URLs:

```typescript
// frontend/app/page.tsx
const API_URL = process.env.NEXT_PUBLIC_API_URL || ''

// Makes request to same domain: /api/listings/
await axios.get(`${API_URL}/api/listings/`, { params })
```

Since `NEXT_PUBLIC_API_URL` defaults to empty string, all API calls are relative to the same domain where the frontend is served.

## API Endpoints

### Listings
- `GET /api/listings/` - Get all listings with filters and pagination
- `GET /api/listings/{id}` - Get specific listing by ID
- `GET /api/listings/stats/overview` - Get statistics overview
- `GET /api/listings/filter-options/makes` - Get available car makes
- `GET /api/listings/filter-options/series/{make_id}` - Get series for a make
- `GET /api/listings/filter-options/models/{make_id}` - Get models for a make
- `GET /api/listings/filter-options/fuel-types` - Get available fuel types
- `GET /api/listings/filter-options/body-types` - Get available body types

### Comparison
- `GET /api/comparison/compare` - Compare cars by make and model
- `GET /api/comparison/similar/{listing_id}` - Find similar listings

### Health
- `GET /health` - Health check
- `GET /api` - API information

## Environment Configuration

### Production (Docker)
No configuration needed! The frontend and backend are bundled together.

```bash
docker-compose up
```

Access the application at: http://localhost:8000

### Development

#### Backend Development
```bash
cd backend
python -m uvicorn app.main:app --reload --port 8000
```

#### Frontend Development
```bash
cd frontend
npm install
npm run dev  # Runs on port 3000
```

Create `frontend/.env.local`:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

This configures the frontend to call the backend on port 8000.

## CORS Configuration

The backend is configured to accept requests from any origin by default:

```python
# backend/app/config.py
cors_origins: List[str] = ["*"]
```

You can restrict this in `.env.api`:
```env
APP_CORS_ORIGINS=["http://localhost:3000","https://yourdomain.com"]
```

## Troubleshooting

### Frontend Not Loading
- Check if frontend build exists: `docker exec car_marketplace_api ls -la /app/static/frontend`
- Check API logs: `docker logs car_marketplace_api`

### API Calls Failing
- Check browser console for errors
- Verify API is running: `curl http://localhost:8000/health`
- Check CORS configuration if using separate frontend

### Database Connection Issues
- Ensure MongoDB is healthy: `docker ps` (check status)
- Check connection string in `.env.api`
- View MongoDB logs: `docker logs car_marketplace_mongodb`

## Local Development Without Docker

### Backend
```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export MONGODB_HOST=localhost
export MONGODB_PORT=27017
export MONGODB_DATABASE_NAME=car_index

# Run the API
cd backend
uvicorn app.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install

# Create .env.local with API URL
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local

# Run development server
npm run dev
```

The frontend will run on `http://localhost:3000` and make API calls to `http://localhost:8000`.

## Deployment Notes

### Single Container Deployment
The current setup uses a single container for both frontend and backend, which is:
- ✅ Simple to deploy
- ✅ No CORS issues
- ✅ Single point of entry
- ⚠️ Frontend and backend scale together

### Separate Deployment (Alternative)
If you want to deploy frontend and backend separately:

1. **Backend**: Deploy API container exposing port 8000
2. **Frontend**: Build static files and deploy to CDN/static hosting
3. **Configure**: Set `NEXT_PUBLIC_API_URL=https://your-api-domain.com` in frontend build
4. **CORS**: Update `APP_CORS_ORIGINS` in backend to include frontend domain

## Next Steps

- Access the application: http://localhost:8000
- View API docs: http://localhost:8000/api
- Check MongoDB: http://localhost:8081 (Mongo Express)
- Monitor scraping: `docker logs car_marketplace_cron -f`
