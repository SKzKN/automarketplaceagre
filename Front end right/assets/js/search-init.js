import { getMakes, getModels, getFuelTypes, getBodyTypes } from './api.js';

window.apibaseurl = 'http://localhost:8000'; // <-- Set this!

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
        // Fetch all makes - API returns array directly: [{id, name, is_top}, ...]
        const makesData = await getMakes();
        if (Array.isArray(makesData)) {
            // Separate top brands and others, then sort each group
            const topBrands = makesData.filter(m => m.is_top).sort((a, b) => a.name.localeCompare(b.name));
            const otherBrands = makesData.filter(m => !m.is_top).sort((a, b) => a.name.localeCompare(b.name));
            filterCache.makes = [...topBrands, ...otherBrands];
            
            // Fetch models for ALL makes in parallel
            const modelPromises = filterCache.makes.map(async (make) => {
                try {
                    const modelsData = await getModels(make.id);
                    return { makeId: make.id, models: Array.isArray(modelsData) ? modelsData : [] };
                } catch (error) {
                    console.error(`Error loading models for ${make.name}:`, error);
                    return { makeId: make.id, models: [] };
                }
            });
            
            const allModels = await Promise.all(modelPromises);
            allModels.forEach(({ makeId, models }) => {
                filterCache.modelsByMake[makeId] = models;
            });
        }
        
        // Fetch fuel types - API returns array directly
        const fuelData = await getFuelTypes();
        if (Array.isArray(fuelData)) {
            filterCache.fuelTypes = fuelData.filter(f => f); // Remove null/empty
        }
        
        // Fetch body types - API returns array directly
        const bodyData = await getBodyTypes();
        if (Array.isArray(bodyData)) {
            filterCache.bodyTypes = bodyData.filter(b => b); // Remove null/empty
        }
        
        console.log('Filter data prefetched:', filterCache);
    } catch (error) {
        console.error('Error prefetching filter data:', error);
    }
}

async function populateForm(form) {
  // Populate makes from cache - makes are now objects with {id, name, is_top}
  const makeSelect = form.querySelector('select[name="make"]');
  if (makeSelect) {
    makeSelect.innerHTML = defaultOption('Kõik margid');
    if (filterCache.makes.length) {
      filterCache.makes.forEach(make => {
        if (!make || !make.id) return; // Skip invalid values
        const opt = document.createElement('option');
        opt.value = make.id; // Use make ID as value
        opt.textContent = make.name; // Display make name
        // Optionally add styling for top brands
        if (make.is_top) {
          opt.style.fontWeight = 'bold';
        }
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
        const selectedMakeId = makeSelect.value;
        if (selectedMakeId && filterCache.modelsByMake[selectedMakeId]) {
          filterCache.modelsByMake[selectedMakeId].forEach(model => {
            if (!model || !model.id) return; // Skip invalid values
            const opt = document.createElement('option');
            opt.value = model.id; // Use model ID as value
            opt.textContent = model.name; // Display model name
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
      opt.textContent = fuel; // Display as-is
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
      opt.textContent = body; // Display as-is
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
