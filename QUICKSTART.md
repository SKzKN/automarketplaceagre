# Quick Start Guide

## Getting Started in 3 Steps

### 1. Copy Environment Files

```bash
cp .env.api.template .env.api
cp .env.scrapers.template .env.scrapers
cp .env.mongo-express.template .env.mongo-express
cp .env.ngrok.template .env.ngrok
```

### 2. Start the Application

```bash
docker-compose up
```

This will:
- Start MongoDB database
- Build and serve the Next.js frontend
- Start the FastAPI backend API
- Set up scheduled scraping with cron
- Start Mongo Express (database UI)

### 3. Access the Application

- **Frontend & API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/api
- **MongoDB Admin**: http://localhost:8081
  - Username: `admin`
  - Password: `admin123`

## Run Initial Scraping (Optional)

To populate the database with car listings:

```bash
docker-compose --profile scrapers up scrapers
```

This will:
1. Seed the taxonomy (car makes, models, series)
2. Scrape listings from Auto24, AutoDiiler, and Veego
3. Exit when complete

After this, the cron service will automatically scrape new listings based on the schedule in `.env.scrapers` (default: daily at 2 AM).

## What's Running?

| Service | Port | Description |
|---------|------|-------------|
| **API + Frontend** | 8000 | Next.js UI + FastAPI backend |
| **MongoDB** | 27017 | Database |
| **Mongo Express** | 8081 | Database admin UI |
| **Cron** | - | Scheduled scraping (background) |

## Next Steps

- Browse car listings at http://localhost:8000
- Use filters to search by make, model, price, year, etc.
- Compare cars across different marketplaces
- View statistics and insights

## Troubleshooting

### Services won't start
```bash
# Check service status
docker-compose ps

# View logs  
docker-compose logs -f api
docker-compose logs -f mongodb
```

### No listings showing
Run the initial scraping:
```bash
docker-compose --profile scrapers up scrapers
```

### Port already in use
Edit `compose.yaml` to change port mappings:
```yaml
ports:
  - "8001:8000"  # Change 8000 to 8001
```

## Development Mode

### Backend Development
```bash
# The backend auto-reloads on code changes
# Just edit files in backend/app/ and save

# View logs
docker-compose logs -f api
```

### Frontend Development
If you want to develop the frontend separately:

```bash
cd frontend
npm install
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local
npm run dev  # Runs on port 3000
```

## More Information

- [Frontend-Backend Integration Guide](./FRONTEND_BACKEND_INTEGRATION.md)
- [Full README](./README.md)
