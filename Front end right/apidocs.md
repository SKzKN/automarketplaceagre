# Car Marketplace Aggregator API Documentation
This documentation describes the available API endpoints for the car marketplace aggregator backend, implemented using FastAPI. The endpoints are grouped by resource: Listings and Comparison.

---
### CarListingResponse
Response object for car listings:

- **id**: str (MongoDB ObjectId as string)
- **title**: str
- **make**: str (optional)
- **model**: str (optional)
- **year**: int (optional)
- **price**: float (optional)
- **mileage**: int (optional)
- **fuel_type**: str (optional)
- **transmission**: str (optional)
- **body_type**: str (optional)
- **color**: str (optional)
- **description**: str (optional)
- **image_url**: str (optional)
- **source_url**: str
- **source_site**: str (optional)
- **created_at**: datetime (optional)
- **updated_at**: datetime (optional)

### ComparisonRequest
Request object for car comparison:

- **make**: str
- **model**: str
- **year**: int (optional)


### GET `/api/listings/`
- **Description:** Get car listings with optional filters.
- **Query Parameters:**
  - `query` (string, optional): Search query (searches in title, make, model, description)
  - `make` (string, optional): Car make
  - `model` (string, optional): Car model
  - `min_price` (float, optional): Minimum price
  - `max_price` (float, optional): Maximum price
  - `min_year` (int, optional): Minimum year
  - `max_year` (int, optional): Maximum year
  - `body_type` (string, optional): Body type
  - `fuel_type` (string, optional): Fuel type
  - `source_site` (string, optional): Source site
  - `limit` (int, optional, default=50): Number of results (1-100)
  - `offset` (int, optional, default=0): Pagination offset
- **Response:** List of car listings (CarListingResponse)

### GET `/api/listings/{listing_id}`
- **Description:** Get a single listing by ID.
- **Path Parameters:**
  - `listing_id` (string): Listing ID
- **Response:** Car listing (CarListingResponse)

### GET `/api/listings/stats/overview`
- **Description:** Get overview statistics.
- **Response:**
  - `total_listings`: Total number of listings
  - `by_source`: Listings count by source site
  - `price_stats`: Min, max, avg price
  - `top_makes`: Top 10 car makes by count

### GET `/api/listings/filter-options/makes`
- **Description:** Get all available car makes (database + comprehensive list).
- **Response:** `{ "makes": [ ... ] }`

### GET `/api/listings/filter-options/models`
- **Description:** Get all available models for a given make.
- **Query Parameters:**
  - `make` (string, optional): Car make
- **Response:** `{ "models": [ ... ] }`

### GET `/api/listings/filter-options/fuel-types`
- **Description:** Get all available fuel types from database.
- **Response:** `{ "fuel_types": [ ... ] }`

### GET `/api/listings/filter-options/body-types`
- **Description:** Get all available body types from database.
- **Response:** `{ "body_types": [ ... ] }`

---

## Comparison API

**Base Path:** `/api/comparison`

### GET `/api/comparison/compare`
- **Description:** Compare similar cars from different sources.
- **Query Parameters:**
  - `make` (string, required): Car make
  - `model` (string, required): Car model
  - `year` (int, optional): Year
- **Response:** List of car listings (CarListingResponse)

### GET `/api/comparison/similar/{listing_id}`
- **Description:** Get similar cars to a given listing (same make/model, different sources).
- **Path Parameters:**
  - `listing_id` (string): Listing ID
- **Response:** List of car listings (CarListingResponse)

---

## Models

### CarListingResponse
- The response model for car listings. See `app/models/schemas.py` for details.

---

## Notes
- All endpoints return JSON responses.
- Filtering and searching are case-insensitive where applicable.
- Pagination is supported via `limit` and `offset` parameters.
- For more details on request/response models, see the backend source code and schemas.
