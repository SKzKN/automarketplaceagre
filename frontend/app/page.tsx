'use client'

import { useState, useEffect } from 'react'
import SearchBar from '@/components/SearchBar'
import FilterPanel from '@/components/FilterPanel'
import CarListingCard from '@/components/CarListingCard'
import ComparisonView from '@/components/ComparisonView'
import { CarListing } from '@/types'
import axios from 'axios'

// Use relative URL in production (same domain), absolute for local dev
const API_URL = process.env.NEXT_PUBLIC_API_URL || (typeof window !== 'undefined' ? '' : 'http://localhost:8000')

export default function Home() {
  const [listings, setListings] = useState<CarListing[]>([])
  const [loading, setLoading] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [filters, setFilters] = useState({
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
  const [comparisonMode, setComparisonMode] = useState(false)
  const [comparisonMakeId, setComparisonMakeId] = useState('')
  const [comparisonModelId, setComparisonModelId] = useState('')
  const [offset, setOffset] = useState(0)
  const [hasMore, setHasMore] = useState(true)
  const [totalCount, setTotalCount] = useState(0)
  const limit = 50

  const fetchListings = async (reset = false) => {
    setLoading(true)
    try {
      const currentOffset = reset ? 0 : offset
      const params: any = {
        limit,
        offset: currentOffset,
      }
      if (searchQuery) params.query = searchQuery
      if (filters.makeId) params.make_id = filters.makeId
      if (filters.seriesId) params.series_id = filters.seriesId
      if (filters.modelId) params.model_id = filters.modelId
      if (filters.minPrice) params.min_price = parseFloat(filters.minPrice)
      if (filters.maxPrice) params.max_price = parseFloat(filters.maxPrice)
      if (filters.minYear) params.min_year = parseInt(filters.minYear)
      if (filters.maxYear) params.max_year = parseInt(filters.maxYear)
      if (filters.bodyType) params.body_type = filters.bodyType
      if (filters.fuelType) params.fuel_type = filters.fuelType
      if (filters.sourceSite) params.source_site = filters.sourceSite

      const response = await axios.get(`${API_URL}/api/listings/`, { params })
      const newListings = response.data
      
      if (reset) {
        setListings(newListings)
        setOffset(limit)
      } else {
        setListings([...listings, ...newListings])
        setOffset(offset + limit)
      }
      
      setHasMore(newListings.length === limit)
      setTotalCount(response.headers['x-total-count'] ? parseInt(response.headers['x-total-count']) : newListings.length)
    } catch (error) {
      console.error('Error fetching listings:', error)
    } finally {
      setLoading(false)
    }
  }

  const loadMore = () => {
    if (!loading && hasMore) {
      fetchListings(false)
    }
  }

  const handleComparison = async () => {
    if (!comparisonMakeId || !comparisonModelId) return
    
    setLoading(true)
    try {
      const params: any = {
        make_id: comparisonMakeId,
        model_id: comparisonModelId,
      }
      if (filters.minYear) params.year = parseInt(filters.minYear)

      const response = await axios.get(`${API_URL}/api/comparison/compare`, { params })
      setListings(response.data)
      setComparisonMode(true)
    } catch (error) {
      console.error('Error fetching comparison:', error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (!comparisonMode) {
      setOffset(0)
      setHasMore(true)
      fetchListings(true)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchQuery, JSON.stringify(filters), comparisonMode])

  return (
    <div className="min-h-screen bg-gray-50 pb-8">
      {/* Header */}
      <header className="bg-white shadow-sm sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 sm:py-6">
          <h1 className="text-2xl sm:text-3xl font-bold text-gray-900">Car Index</h1>
          <p className="mt-1 sm:mt-2 text-sm sm:text-base text-gray-600">All Estonian car listings in one place</p>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 sm:py-6 lg:py-8">
        {/* Search and Filter Section */}
        <div className="bg-white rounded-lg shadow-md p-4 sm:p-6 mb-6 sm:mb-8">
          {/* Search Bar */}
          <div className="flex flex-col sm:flex-row gap-3 sm:gap-4 mb-4">
            <div className="flex-1">
              <SearchBar
                value={searchQuery}
                onChange={setSearchQuery}
                onSearch={fetchListings}
              />
            </div>
            <button
              onClick={() => {
                setOffset(0)
                fetchListings(true)
              }}
              className="w-full sm:w-auto px-6 py-2.5 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors font-medium"
            >
              Search
            </button>
          </div>

          {/* Comparison Mode Toggle */}
          <div className="mb-4 p-4 bg-gray-50 rounded-lg">
            <div className="flex flex-col sm:flex-row sm:items-center gap-3 sm:gap-4">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={comparisonMode}
                  onChange={(e) => {
                    setComparisonMode(e.target.checked)
                    if (!e.target.checked) fetchListings()
                  }}
                  className="w-4 h-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                />
                <span className="font-medium text-sm sm:text-base">Comparison Mode</span>
              </label>
              {comparisonMode && (
                <div className="flex flex-col sm:flex-row gap-2 flex-1">
                  <input
                    type="text"
                    placeholder="Make ID"
                    value={comparisonMakeId}
                    onChange={(e) => setComparisonMakeId(e.target.value)}
                    className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent text-sm sm:text-base"
                  />
                  <input
                    type="text"
                    placeholder="Model ID"
                    value={comparisonModelId}
                    onChange={(e) => setComparisonModelId(e.target.value)}
                    className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent text-sm sm:text-base"
                  />
                  <button
                    onClick={handleComparison}
                    className="w-full sm:w-auto px-6 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors font-medium text-sm sm:text-base"
                  >
                    Compare
                  </button>
                </div>
              )}
            </div>
          </div>

          <FilterPanel filters={filters} onChange={setFilters} />
        </div>

        {/* Results */}
        {loading ? (
          <div className="text-center py-12">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
            <p className="mt-4 text-gray-600">Loading listings...</p>
          </div>
        ) : comparisonMode ? (
          <ComparisonView listings={listings} />
        ) : (
          <div>
            <div className="mb-4 text-sm sm:text-base text-gray-600">
              Showing {listings.length} {listings.length === 1 ? 'listing' : 'listings'}
              {totalCount > listings.length && ` of ${totalCount}`}
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6">
              {listings.map((listing) => (
                <CarListingCard key={listing.id} listing={listing} />
              ))}
            </div>
            {listings.length === 0 && !loading && (
              <div className="text-center py-12 text-gray-500">
                No listings found. Try adjusting your search or filters.
              </div>
            )}
            {hasMore && (
              <div className="mt-8 text-center">
                <button
                  onClick={loadMore}
                  disabled={loading}
                  className="px-6 py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors font-medium disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {loading ? 'Loading...' : 'Load More'}
                </button>
              </div>
            )}
            {!hasMore && listings.length > 0 && (
              <div className="mt-6 text-center text-sm text-gray-500">
                All listings loaded
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  )
}

