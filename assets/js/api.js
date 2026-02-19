// Car Marketplace Aggregator API Client
// Set this variable to your backend API base URL, e.g. 'http://localhost:8000' or your deployed endpoint
let apibaseurl = 'https://car-index.fly.dev';

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
    return await apiGet('/api/listings/filter-options/makes');
}
export async function getModels(make) {
    return await apiGet('/api/listings/filter-options/models', { make });
}
export async function getFuelTypes() {
    return await apiGet('/api/listings/filter-options/fuel-types');
}
export async function getBodyTypes() {
    return await apiGet('/api/listings/filter-options/body-types');
}

// Comparison
export async function compareCars({ make, model, year }) {
    return await apiGet('/api/comparison/compare', { make, model, year });
}
export async function getSimilarCars(listing_id) {
    return await apiGet(`/api/comparison/similar/${listing_id}`);
}

// Example: set apibaseurl in your main JS file before using
// apibaseurl = 'http://localhost:8000';
// getListings({ make: 'Toyota', min_price: 10000 }).then(console.log);