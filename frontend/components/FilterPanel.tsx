'use client'

import { Filters, MakeDTO, SeriesDTO, ModelDTO } from '@/types'
import { useState, useEffect } from 'react'
import axios from 'axios'

interface FilterPanelProps {
  filters: Filters
  onChange: (filters: Filters) => void
}

// Use relative URL in production (same domain), absolute for local dev
const API_URL = process.env.NEXT_PUBLIC_API_URL || (typeof window !== 'undefined' ? '' : 'http://localhost:8000')

export default function FilterPanel({ filters, onChange }: FilterPanelProps) {
  const [makes, setMakes] = useState<MakeDTO[]>([])
  const [series, setSeries] = useState<SeriesDTO[]>([])
  const [models, setModels] = useState<ModelDTO[]>([])
  const [fuelTypes, setFuelTypes] = useState<string[]>([])
  const [bodyTypes, setBodyTypes] = useState<string[]>([])
  const [loadingMakes, setLoadingMakes] = useState(false)
  const [loadingSeries, setLoadingSeries] = useState(false)
  const [loadingModels, setLoadingModels] = useState(false)
  const [loadingFuelTypes, setLoadingFuelTypes] = useState(false)
  const [loadingBodyTypes, setLoadingBodyTypes] = useState(false)

  // Get display names for selected values
  const selectedMake = makes.find(m => m.id === filters.makeId)
  const selectedSeries = series.find(s => s.id === filters.seriesId)
  const selectedModel = models.find(m => m.id === filters.modelId)

  // Fetch makes on component mount
  useEffect(() => {
    const fetchMakes = async () => {
      setLoadingMakes(true)
      try {
        const response = await axios.get(`${API_URL}/api/listings/filter-options/makes`)
        setMakes(response.data || [])
      } catch (error) {
        console.error('Error fetching makes:', error)
      } finally {
        setLoadingMakes(false)
      }
    }
    fetchMakes()
  }, [])

  // Fetch fuel types on component mount
  useEffect(() => {
    const fetchFuelTypes = async () => {
      setLoadingFuelTypes(true)
      try {
        const response = await axios.get(`${API_URL}/api/listings/filter-options/fuel-types`)
        setFuelTypes(response.data.fuel_types || [])
      } catch (error) {
        console.error('Error fetching fuel types:', error)
      } finally {
        setLoadingFuelTypes(false)
      }
    }
    fetchFuelTypes()
  }, [])

  // Fetch body types on component mount
  useEffect(() => {
    const fetchBodyTypes = async () => {
      setLoadingBodyTypes(true)
      try {
        const response = await axios.get(`${API_URL}/api/listings/filter-options/body-types`)
        setBodyTypes(response.data.body_types || [])
      } catch (error) {
        console.error('Error fetching body types:', error)
      } finally {
        setLoadingBodyTypes(false)
      }
    }
    fetchBodyTypes()
  }, [])

  // Fetch series when make changes
  useEffect(() => {
    const fetchSeries = async () => {
      if (!filters.makeId) {
        setSeries([])
        return
      }

      setLoadingSeries(true)
      try {
        const response = await axios.get(`${API_URL}/api/listings/filter-options/series/${filters.makeId}`)
        setSeries(response.data || [])
      } catch (error) {
        console.error('Error fetching series:', error)
        setSeries([])
      } finally {
        setLoadingSeries(false)
      }
    }
    fetchSeries()
  }, [filters.makeId])

  // Fetch models when make or series changes
  useEffect(() => {
    const fetchModels = async () => {
      if (!filters.makeId) {
        setModels([])
        return
      }

      setLoadingModels(true)
      try {
        const params: { series_id?: string } = {}
        if (filters.seriesId) {
          params.series_id = filters.seriesId
        }
        const response = await axios.get(`${API_URL}/api/listings/filter-options/models/${filters.makeId}`, { params })
        setModels(response.data || [])
      } catch (error) {
        console.error('Error fetching models:', error)
        setModels([])
      } finally {
        setLoadingModels(false)
      }
    }
    fetchModels()
  }, [filters.makeId, filters.seriesId])

  const updateFilter = (key: keyof Filters, value: string) => {
    const updatedFilters = { ...filters, [key]: value }
    
    // Cascade resets when parent selections change
    if (key === 'makeId') {
      updatedFilters.seriesId = ''
      updatedFilters.modelId = ''
    }
    if (key === 'seriesId') {
      updatedFilters.modelId = ''
    }
    
    onChange(updatedFilters)
  }

  const resetFilters = () => {
    onChange({
      makeId: '',
      seriesId: '',
      modelId: '',
      minPrice: '',
      maxPrice: '',
      minYear: '',
      maxYear: '',
      bodyType: '',
      fuelType: '',
      sourceSite: '',
    })
    setSeries([])
    setModels([])
  }

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
        {/* Make Selector */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1.5">Make</label>
          <select
            value={filters.makeId}
            onChange={(e) => updateFilter('makeId', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm sm:text-base focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            disabled={loadingMakes}
          >
            <option value="">Any Make</option>
            {/* Top brands section */}
            {makes.filter(m => m.is_top).length > 0 && (
              <optgroup label="Popular Brands">
                {makes.filter(m => m.is_top).map((make) => (
                  <option key={make.id} value={make.id}>
                    {make.name}
                  </option>
                ))}
              </optgroup>
            )}
            {/* Other brands section */}
            {makes.filter(m => !m.is_top).length > 0 && (
              <optgroup label="All Brands">
                {makes.filter(m => !m.is_top).map((make) => (
                  <option key={make.id} value={make.id}>
                    {make.name}
                  </option>
                ))}
              </optgroup>
            )}
          </select>
        </div>

        {/* Series Selector */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1.5">Series</label>
          <select
            value={filters.seriesId}
            onChange={(e) => updateFilter('seriesId', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm sm:text-base focus:ring-2 focus:ring-primary-500 focus:border-transparent disabled:bg-gray-100"
            disabled={loadingSeries || !filters.makeId || series.length === 0}
          >
            <option value="">{!filters.makeId ? 'Select Make First' : series.length === 0 ? 'No Series Available' : 'Any Series'}</option>
            {series.map((s) => (
              <option key={s.id} value={s.id}>
                {s.name}
              </option>
            ))}
          </select>
        </div>

        {/* Model Selector */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1.5">Model</label>
          <select
            value={filters.modelId}
            onChange={(e) => updateFilter('modelId', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm sm:text-base focus:ring-2 focus:ring-primary-500 focus:border-transparent disabled:bg-gray-100"
            disabled={loadingModels || !filters.makeId}
          >
            <option value="">{!filters.makeId ? 'Select Make First' : 'Any Model'}</option>
            {models.map((model) => (
              <option key={model.id} value={model.id}>
                {model.name}
              </option>
            ))}
          </select>
        </div>

        {/* Price Range */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1.5">Min Price (€)</label>
          <input
            type="number"
            value={filters.minPrice}
            onChange={(e) => updateFilter('minPrice', e.target.value)}
            placeholder="0"
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm sm:text-base focus:ring-2 focus:ring-primary-500 focus:border-transparent"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1.5">Max Price (€)</label>
          <input
            type="number"
            value={filters.maxPrice}
            onChange={(e) => updateFilter('maxPrice', e.target.value)}
            placeholder="100000"
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm sm:text-base focus:ring-2 focus:ring-primary-500 focus:border-transparent"
          />
        </div>

        {/* Year Range */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1.5">Min Year</label>
          <input
            type="number"
            value={filters.minYear}
            onChange={(e) => updateFilter('minYear', e.target.value)}
            placeholder="2000"
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm sm:text-base focus:ring-2 focus:ring-primary-500 focus:border-transparent"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1.5">Max Year</label>
          <input
            type="number"
            value={filters.maxYear}
            onChange={(e) => updateFilter('maxYear', e.target.value)}
            placeholder="2024"
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm sm:text-base focus:ring-2 focus:ring-primary-500 focus:border-transparent"
          />
        </div>

        {/* Body Type */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1.5">Body Type</label>
          <select
            value={filters.bodyType}
            onChange={(e) => updateFilter('bodyType', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm sm:text-base focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            disabled={loadingBodyTypes}
          >
            <option value="">Any</option>
            {bodyTypes.map((bodyType) => (
              <option key={bodyType} value={bodyType}>
                {bodyType}
              </option>
            ))}
          </select>
        </div>

        {/* Fuel Type */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1.5">Fuel Type</label>
          <select
            value={filters.fuelType}
            onChange={(e) => updateFilter('fuelType', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm sm:text-base focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            disabled={loadingFuelTypes}
          >
            <option value="">Any</option>
            {fuelTypes.map((fuelType) => (
              <option key={fuelType} value={fuelType}>
                {fuelType}
              </option>
            ))}
          </select>
        </div>

        {/* Source Site */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1.5">Source Site</label>
          <select
            value={filters.sourceSite}
            onChange={(e) => updateFilter('sourceSite', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm sm:text-base focus:ring-2 focus:ring-primary-500 focus:border-transparent"
          >
            <option value="">All Sources</option>
            <option value="autodiiler">autodiiler.ee</option>
            <option value="auto24">Auto24.ee</option>
            <option value="veego">veego.ee</option>
          </select>
        </div>
      </div>
      
      {/* Active Filters Summary */}
      {(selectedMake || selectedSeries || selectedModel) && (
        <div className="flex flex-wrap gap-2 text-sm">
          <span className="text-gray-500">Active filters:</span>
          {selectedMake && (
            <span className="px-2 py-1 bg-primary-100 text-primary-800 rounded-full">
              {selectedMake.name}
            </span>
          )}
          {selectedSeries && (
            <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded-full">
              {selectedSeries.name}
            </span>
          )}
          {selectedModel && (
            <span className="px-2 py-1 bg-green-100 text-green-800 rounded-full">
              {selectedModel.name}
            </span>
          )}
        </div>
      )}
      
      <div className="flex justify-end">
        <button
          onClick={resetFilters}
          className="w-full sm:w-auto px-4 py-2 text-sm text-white bg-red-600 rounded-lg hover:bg-red-700 transition-colors font-medium"
        >
          Reset Filters
        </button>
      </div>
    </div>
  )
}

