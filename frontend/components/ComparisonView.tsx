'use client'

import { CarListing } from '@/types'
import { ExternalLink } from 'lucide-react'

interface ComparisonViewProps {
  listings: CarListing[]
}

export default function ComparisonView({ listings }: ComparisonViewProps) {
  // Group listings by source site
  const groupedBySource = listings.reduce((acc, listing) => {
    if (!acc[listing.source_site]) {
      acc[listing.source_site] = []
    }
    acc[listing.source_site].push(listing)
    return acc
  }, {} as Record<string, CarListing[]>)

  const formatPrice = (price: number | null) => {
    if (!price) return 'N/A'
    return new Intl.NumberFormat('et-EE', {
      style: 'currency',
      currency: 'EUR',
      maximumFractionDigits: 0,
    }).format(price)
  }

  const getSourceName = (source: string) => {
    const names: Record<string, string> = {
      auto24: 'Auto24.ee',
      autodiiler: 'autodiiler.ee',
      veego: 'veego.ee',
      okidoki: 'okidoki.ee',
    }
    return names[source] || source
  }

  if (listings.length === 0) {
    return (
      <div className="text-center py-12 text-gray-500">
        No listings found for comparison. Try a different make/model.
      </div>
    )
  }

  // Get common make/model for header
  const firstListing = listings[0]
  const comparisonTitle = `${firstListing.make || ''} ${firstListing.model || ''}`.trim()

  return (
    <div>
      <div className="mb-4 sm:mb-6">
        <h2 className="text-xl sm:text-2xl font-bold text-gray-900 mb-2">
          Comparing: {comparisonTitle}
        </h2>
        <p className="text-sm sm:text-base text-gray-600">
          Found {listings.length} {listings.length === 1 ? 'listing' : 'listings'} across {Object.keys(groupedBySource).length} sources
        </p>
      </div>

      {/* Side-by-side comparison by source */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6 mb-6 sm:mb-8">
        {Object.entries(groupedBySource).map(([source, sourceListings]) => (
          <div key={source} className="bg-white rounded-lg shadow-md p-4">
            <h3 className="font-semibold text-lg mb-3 text-primary-600">
              {getSourceName(source)}
            </h3>
            <div className="text-sm text-gray-500 mb-3">
              {sourceListings.length} {sourceListings.length === 1 ? 'listing' : 'listings'}
            </div>
            <div className="space-y-2">
              {sourceListings.slice(0, 3).map((listing) => (
                <div key={listing.id} className="border-b pb-2 last:border-0">
                  <div className="font-medium text-sm mb-1 line-clamp-2">
                    {listing.title}
                  </div>
                  <div className="text-lg font-bold text-primary-600 mb-1">
                    {formatPrice(listing.price)}
                  </div>
                  {listing.year && (
                    <div className="text-xs text-gray-500">
                      {listing.year}
                      {listing.mileage && ` • ${listing.mileage.toLocaleString()} km`}
                    </div>
                  )}
                  <a
                    href={listing.source_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-xs text-primary-600 hover:text-primary-700 flex items-center gap-1 mt-1"
                  >
                    View <ExternalLink className="w-3 h-3" />
                  </a>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>

      {/* Detailed list view - mobile cards, desktop table */}
      <div className="bg-white rounded-lg shadow-md overflow-hidden">
        <div className="px-4 sm:px-6 py-3 sm:py-4 bg-gray-50 border-b">
          <h3 className="font-semibold text-base sm:text-lg">All Listings</h3>
        </div>
        
        {/* Mobile: Card view */}
        <div className="block sm:hidden divide-y divide-gray-200">
          {listings.map((listing) => (
            <div key={listing.id} className="p-4">
              <div className="font-medium text-sm text-gray-900 mb-2">{listing.title}</div>
              <div className="flex flex-wrap gap-x-4 gap-y-2 text-xs text-gray-600 mb-3">
                <span className="font-medium text-primary-600">{formatPrice(listing.price)}</span>
                <span>{getSourceName(listing.source_site)}</span>
                {listing.year && <span>{listing.year}</span>}
                {listing.mileage && <span>{listing.mileage.toLocaleString()} km</span>}
              </div>
              <a
                href={listing.source_url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1 text-xs text-primary-600 hover:text-primary-700 font-medium"
              >
                View Original <ExternalLink className="w-3 h-3" />
              </a>
            </div>
          ))}
        </div>
        
        {/* Desktop: Table view */}
        <div className="hidden sm:block overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 lg:px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Title
                </th>
                <th className="px-4 lg:px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Source
                </th>
                <th className="px-4 lg:px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Price
                </th>
                <th className="px-4 lg:px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Year
                </th>
                <th className="px-4 lg:px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Mileage
                </th>
                <th className="px-4 lg:px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Link
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {listings.map((listing) => (
                <tr key={listing.id} className="hover:bg-gray-50">
                  <td className="px-4 lg:px-6 py-4">
                    <div className="text-sm font-medium text-gray-900">{listing.title}</div>
                  </td>
                  <td className="px-4 lg:px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-500">{getSourceName(listing.source_site)}</div>
                  </td>
                  <td className="px-4 lg:px-6 py-4 whitespace-nowrap">
                    <div className="text-sm font-semibold text-primary-600">
                      {formatPrice(listing.price)}
                    </div>
                  </td>
                  <td className="px-4 lg:px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-500">{listing.year || 'N/A'}</div>
                  </td>
                  <td className="px-4 lg:px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-500">
                      {listing.mileage ? `${listing.mileage.toLocaleString()} km` : 'N/A'}
                    </div>
                  </td>
                  <td className="px-4 lg:px-6 py-4 whitespace-nowrap">
                    <a
                      href={listing.source_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-primary-600 hover:text-primary-700 flex items-center gap-1 text-sm"
                    >
                      View <ExternalLink className="w-4 h-4" />
                    </a>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

