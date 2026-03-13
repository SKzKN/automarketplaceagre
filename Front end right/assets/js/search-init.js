import { getMakes, getAllModels, getFuelTypes, getBodyTypes, getListingsCount } from './api.js';

window.apibaseurl = 'https://automarketplaceagre.onrender.com';

// Cache for all filter data (prefetched)
const filterCache = {
    makes: [],
    modelsByMake: {},
    fuelTypes: [],
    bodyTypes: []
};

const PRIORITY_BODY_TYPES = [
  'universaal',
  'sedaan',
  'kupee',
  'luukpära',
  'mahtuniversaal',
  'kabriolett',
  'pikap',
  'limusiin'
];

// Helper to populate select options
const defaultOption = (label = 'Kõik') => `<option value="">${label}</option>`;

function sortBodyTypesForDropdown(bodyTypes = []) {
  const uniqueBodyTypes = [...new Set(bodyTypes.filter(Boolean).map(b => b.toLowerCase()))];

  const prioritized = PRIORITY_BODY_TYPES.filter(type => uniqueBodyTypes.includes(type));
  const rest = uniqueBodyTypes
    .filter(type => !PRIORITY_BODY_TYPES.includes(type))
    .sort((a, b) => a.localeCompare(b, 'et'));

  return [...prioritized, ...rest];
}

function enableTypeSearchForSelect(selectElement) {
  if (!selectElement || selectElement.dataset.typeSearchEnabled === 'true') return;

  let searchBuffer = '';
  let resetTimer = null;

  const handleKeydown = (event) => {
    if (event.altKey || event.ctrlKey || event.metaKey) return;

    const isCharacter = event.key && event.key.length === 1;
    const isBackspace = event.key === 'Backspace';
    if (!isCharacter && !isBackspace) return;

    if (isBackspace) {
      searchBuffer = searchBuffer.slice(0, -1);
    } else {
      searchBuffer += event.key.toLowerCase();
    }

    if (resetTimer) clearTimeout(resetTimer);
    resetTimer = setTimeout(() => {
      searchBuffer = '';
    }, 800);

    if (!searchBuffer) return;

    const options = Array.from(selectElement.options).filter(option => option.value !== '');
    const match = options.find(option => option.textContent.toLowerCase().includes(searchBuffer));
    if (match && selectElement.value !== match.value) {
      selectElement.value = match.value;
      selectElement.dispatchEvent(new Event('change', { bubbles: true }));
    }

    event.preventDefault();
  };

  selectElement.addEventListener('keydown', handleKeydown);
  selectElement.dataset.typeSearchEnabled = 'true';

  setTimeout(() => {
    const wrapper = selectElement.nextElementSibling;
    if (wrapper && wrapper.classList.contains('nice-select') && wrapper.dataset.typeSearchEnabled !== 'true') {
      wrapper.addEventListener('keydown', handleKeydown);
      wrapper.dataset.typeSearchEnabled = 'true';
    }
  }, 0);
}

const normalizeBrandKey = (value = '') => value
  .toString()
  .trim()
  .toLowerCase()
  .replace(/&/g, 'and')
  .replace(/[^a-z0-9]+/g, '-');

function findMakeByBrandKey(brandKey) {
  const normalizedBrandKey = normalizeBrandKey(brandKey);
  return filterCache.makes.find(make => {
    if (!make || !make.id || !make.name) return false;
    const normalizedName = normalizeBrandKey(make.name);
    return normalizedName === normalizedBrandKey;
  }) || null;
}

function initQuickBrandButtons() {
  const brandButtons = document.querySelectorAll('.brand-filter-btn');
  if (!brandButtons.length) return;

  brandButtons.forEach(button => {
    button.addEventListener('click', () => {
      const brandKey = button.dataset.brand || button.textContent || '';
      const make = findMakeByBrandKey(brandKey);

      if (!make) {
        console.warn(`Quick brand button could not resolve make: ${brandKey}`);
        return;
      }

      const params = new URLSearchParams({ make: make.id });
      window.location.href = 'search-results.html?' + params.toString();
    });
  });
}

async function updateHeroListingsCount() {
  const countElement = document.getElementById('hero-listings-count');
  if (!countElement) return;

  try {
    const totalCount = await getListingsCount();
    countElement.textContent = totalCount.toLocaleString('et-EE');
  } catch (error) {
    console.error('Error loading hero listings count:', error);
    countElement.textContent = '...';
  }
}

// Prefetch ALL filter data at once
async function prefetchFilterData() {
    try {
        // Fetch makes and all models up front to avoid one request per make.
        const [makesData, allModelsData] = await Promise.all([
            getMakes(),
            getAllModels()
        ]);

        if (Array.isArray(makesData)) {
            // Separate top brands and others, then sort each group
            const topBrands = makesData.filter(m => m.is_top).sort((a, b) => a.name.localeCompare(b.name));
            const otherBrands = makesData.filter(m => !m.is_top).sort((a, b) => a.name.localeCompare(b.name));
            filterCache.makes = [...topBrands, ...otherBrands];
        }

        if (Array.isArray(allModelsData)) {
            allModelsData.forEach(model => {
                if (!model || !model.make_id) return;
                if (!filterCache.modelsByMake[model.make_id]) {
                    filterCache.modelsByMake[model.make_id] = [];
                }
                filterCache.modelsByMake[model.make_id].push(model);
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
    enableTypeSearchForSelect(makeSelect);
    
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
        enableTypeSearchForSelect(modelSelect);
      });

      enableTypeSearchForSelect(modelSelect);
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
    const orderedBodyTypes = sortBodyTypesForDropdown(filterCache.bodyTypes);
    orderedBodyTypes.forEach(body => {
      if (!body) return; // Skip null/empty values
      const opt = document.createElement('option');
      opt.value = body; // Use exact value from API
      opt.textContent = body; // Display as-is
      if (PRIORITY_BODY_TYPES.includes(body)) {
        opt.style.fontWeight = '700';
      }
      bodySelect.appendChild(opt);
    });
  }
}

// Populate all search forms on page
async function initSearchForms() {
  // First, prefetch all filter data
  await Promise.all([
    prefetchFilterData(),
    updateHeroListingsCount()
  ]);
  initQuickBrandButtons();
  
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
