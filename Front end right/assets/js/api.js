// Car Marketplace Aggregator API Client
// Set this variable to your backend API base URL, e.g. 'http://localhost:8000' or your deployed endpoint
// PRODUCTION: Railway backend URL
let apibaseurl = 'https://automarketplaceagre-production.up.railway.app';

// Helper for GET requests
async function apiGet(path, params = {}) {
    const url = new URL(apibaseurl + path);
    Object.keys(params).forEach(key => {
        if (params[key] !== undefined && params[key] !== '') {
            url.searchParams.append(key, params[key]);
        }
    });
    const res = await fetch(url, { credentials: 'same-origin' });
    if (!res.ok) throw new Error('API error: ' + res.status);
    return await res.json();
}

// Listings
export async function getListings(params = {}) {
    return await apiGet('/api/listings/', params);
}
export async function getListingById(listing_id) {
    return await apiGet(`/api/listings/${listing_id}`);
}
export async function getListingsStats() {
    return await apiGet('/api/listings/stats/overview');
}
export async function getMakes() {
    const response = await apiGet('/api/listings/filter-options/makes');
    // New backend returns List[MakeDTO] with id, name, is_top
    return response;
}
export async function getSeries(make_id) {
    // New endpoint: returns List[SeriesDTO] with id, name, make_id
    return await apiGet(`/api/listings/filter-options/series/${make_id}`);
}
export async function getModels(make_id, series_id = null) {
    // Updated: make_id is now a path parameter, series_id is optional query param
    const params = series_id ? { series_id } : {};
    return await apiGet(`/api/listings/filter-options/models/${make_id}`, params);
}
export async function getFuelTypes() {
    const response = await apiGet('/api/listings/filter-options/fuel-types');
    // Backend returns {"fuel_types": [...]}
    return response.fuel_types || response;
}
export async function getBodyTypes() {
    const response = await apiGet('/api/listings/filter-options/body-types');
    // Backend returns {"body_types": [...]}
    return response.body_types || response;
}

// Comparison
export async function compareCars({ make_id, model_id, year }) {
    // Updated: use make_id and model_id to match new backend
    return await apiGet('/api/comparison/compare', { make_id, model_id, year });
}
export async function getSimilarCars(listing_id) {
    return await apiGet(`/api/comparison/similar/${listing_id}`);
}

// Example: set apibaseurl in your main JS file before using
// apibaseurl = 'http://localhost:8000';
// getListings({ make_id: 'toyota', min_price: 10000 }).then(console.log);