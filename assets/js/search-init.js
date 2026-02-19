import { getMakes, getModels, getFuelTypes, getBodyTypes } from './api.js';

window.apibaseurl = 'https://car-index.fly.dev'; // <-- Set this!

// Cache for all filter data (prefetched)
const filterCache = {
    makes: [],
    modelsByMake: {},
    fuelTypes: [],
    bodyTypes: []
};

// Helper to populate select options
const defaultOption = (label = 'Kõik') => `<option value="">${label}</option>`;

// Prefetch ALL filter data at once
async function prefetchFilterData() {
    try {
        // Fetch all makes
        const makesData = await getMakes();
        if (makesData.makes) {
            filterCache.makes = makesData.makes;
            
            // Fetch models for ALL makes in parallel
            const modelPromises = makesData.makes.map(async (make) => {
                try {
                    const modelsData = await getModels(make);
                    return { make, models: modelsData.models || [] };
                } catch (error) {
                    console.error(`Error loading models for ${make}:`, error);
                    return { make, models: [] };
                }
            });
            
            const allModels = await Promise.all(modelPromises);
            allModels.forEach(({ make, models }) => {
                filterCache.modelsByMake[make] = models;
            });
        }
        
        // Fetch fuel types
        const fuelData = await getFuelTypes();
        if (fuelData.fuel_types) {
            filterCache.fuelTypes = fuelData.fuel_types;
        }
        
        // Fetch body types
        const bodyData = await getBodyTypes();
        if (bodyData.body_types) {
            filterCache.bodyTypes = bodyData.body_types;
        }
        
        console.log('Filter data prefetched:', filterCache);
    } catch (error) {
        console.error('Error prefetching filter data:', error);
    }
}

async function populateForm(form) {
  // Populate makes from cache
  const makeSelect = form.querySelector('select[name="make"]');
  if (makeSelect) {
    makeSelect.innerHTML = defaultOption('Kõik margid');
    if (filterCache.makes.length) {
      filterCache.makes.forEach(make => {
        if (!make) return; // Skip null/empty values
        const opt = document.createElement('option');
        opt.value = make; // Use exact value from API
        // Display text: capitalize first letter of each word
        const displayText = make.split(' ').map(word => 
          word.charAt(0).toUpperCase() + word.slice(1).toLowerCase()
        ).join(' ');
        opt.textContent = displayText;
        makeSelect.appendChild(opt);
      });
    }
    
    // Set up model dropdown
    const modelSelect = form.querySelector('select[name="model"]');
    if (modelSelect) {
      modelSelect.innerHTML = defaultOption('Kõik mudelid');
      
      // Update models when make changes (from cache)
      makeSelect.addEventListener('change', () => {
        modelSelect.innerHTML = defaultOption('Kõik mudelid');
        const selectedMake = makeSelect.value;
        if (selectedMake && filterCache.modelsByMake[selectedMake]) {
          filterCache.modelsByMake[selectedMake].forEach(model => {
            if (!model) return; // Skip null/empty values
            const opt = document.createElement('option');
            opt.value = model; // Use exact value from API
            // Display text: capitalize first letter of each word
            const displayText = model.split(' ').map(word => 
              word.charAt(0).toUpperCase() + word.slice(1).toLowerCase()
            ).join(' ');
            opt.textContent = displayText;
            modelSelect.appendChild(opt);
          });
        }
      });
    }
  }
  
  // Populate fuel types from cache
  const fuelSelect = form.querySelector('select[name="fuel"]');
  if (fuelSelect && filterCache.fuelTypes.length) {
    fuelSelect.innerHTML = defaultOption('Kõik kütused');
    filterCache.fuelTypes.forEach(fuel => {
      if (!fuel) return; // Skip null/empty values
      const opt = document.createElement('option');
      opt.value = fuel; // Use exact value from API
      // Display text: capitalize first letter
      const displayText = fuel.charAt(0).toUpperCase() + fuel.slice(1).toLowerCase();
      opt.textContent = displayText;
      fuelSelect.appendChild(opt);
    });
  }
  
  // Populate body types from cache
  const bodySelect = form.querySelector('select[name="body_type"]');
  if (bodySelect && filterCache.bodyTypes.length) {
    bodySelect.innerHTML = defaultOption('Kõik keretüübid');
    filterCache.bodyTypes.forEach(body => {
      if (!body) return; // Skip null/empty values
      const opt = document.createElement('option');
      opt.value = body; // Use exact value from API
      // Display text: capitalize first letter of each word
      const displayText = body.split(' ').map(word => 
        word.charAt(0).toUpperCase() + word.slice(1).toLowerCase()
      ).join(' ');
      opt.textContent = displayText;
      bodySelect.appendChild(opt);
    });
  }
}

// Populate all search forms on page
async function initSearchForms() {
  // First, prefetch all filter data
  await prefetchFilterData();
  
  const forms = document.querySelectorAll('.search-form');
  for (const form of forms) {
    await populateForm(form);
    form.addEventListener('submit', function(e) {
      e.preventDefault();
      const params = new URLSearchParams();
      for (const el of form.elements) {
        if (el.name && el.value !== '') params.append(el.name, el.value);
      }
      window.location.href = 'search-results.html?' + params.toString();
    });
  }
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initSearchForms);
} else {
  initSearchForms();
}
