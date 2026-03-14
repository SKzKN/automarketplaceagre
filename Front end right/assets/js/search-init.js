import { getMakes, getAllModels, getSeries, getFuelTypes, getBodyTypes, getListingsCount } from './api.js';

window.apibaseurl = 'https://automarketplaceagre.onrender.com';

// Cache for all filter data (prefetched)
const filterCache = {
    makes: [],
  seriesByMake: {},
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
  async function ensureSeriesForMake(makeId) {
    if (!makeId) return [];
    if (!filterCache.seriesByMake[makeId]) {
      try {
        const seriesData = await getSeries(makeId);
        filterCache.seriesByMake[makeId] = Array.isArray(seriesData) ? seriesData : [];
      } catch (error) {
        console.error('Error loading series for make:', error);
        filterCache.seriesByMake[makeId] = [];
      }
    }
    return filterCache.seriesByMake[makeId];
  }

  async function updateModelDropdown(modelSelect, makeId) {
    modelSelect.innerHTML = defaultOption('Kõik mudelid');
    if (!makeId) {
      enableTypeSearchForSelect(modelSelect);
      return;
    }

    const [seriesList, allModelsForMake] = await Promise.all([
      ensureSeriesForMake(makeId),
      Promise.resolve(filterCache.modelsByMake[makeId] || [])
    ]);

    const seriesMap = {};
    seriesList.forEach(series => {
      if (series?.id) seriesMap[series.id] = series.name || '';
    });

    const orderedSeries = [...seriesList].sort((a, b) =>
      (a.name || '').localeCompare(b.name || '', 'et')
    );

    orderedSeries.forEach(series => {
      if (!series?.id) return;

      const seriesOption = document.createElement('option');
      seriesOption.value = `series:${series.id}`;
      seriesOption.textContent = `${series.name} (kõik)`;
      modelSelect.appendChild(seriesOption);

      const modelsInSeries = allModelsForMake
        .filter(model => model?.series_id === series.id)
        .sort((a, b) => (a.name || '').localeCompare(b.name || '', 'et'));

      modelsInSeries.forEach(model => {
        if (!model?.id) return;
        const modelOption = document.createElement('option');
        modelOption.value = model.id;
        modelOption.textContent = model.name;
        modelSelect.appendChild(modelOption);
      });
    });

    const modelsWithoutSeries = allModelsForMake
      .filter(model => model && model.id && !model.series_id)
      .sort((a, b) => (a.name || '').localeCompare(b.name || '', 'et'));

    modelsWithoutSeries.forEach(model => {
      const modelOption = document.createElement('option');
      modelOption.value = model.id;
      modelOption.textContent = model.name;
      modelSelect.appendChild(modelOption);
    });

    enableTypeSearchForSelect(modelSelect);
  }

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
      
      // Update models when make changes (from cache + series)
      makeSelect.addEventListener('change', async () => {
        const selectedMakeId = makeSelect.value;
        await updateModelDropdown(modelSelect, selectedMakeId);
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
        if (!el.name || el.value === '') continue;

        if (el.name === 'model' && typeof el.value === 'string' && el.value.startsWith('series:')) {
          params.append('series', el.value.slice('series:'.length));
          continue;
        }

        params.append(el.name, el.value);
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
