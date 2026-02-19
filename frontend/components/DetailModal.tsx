'use client'

import { X, ExternalLink, MapPin } from 'lucide-react'
import { CarListing } from '@/types'
import { useEffect } from 'react'

interface DetailModalProps {
  listing: CarListing
  onClose: () => void
}

export default function DetailModal({ listing, onClose }: DetailModalProps) {
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose()
      }
    }
    document.addEventListener('keydown', handleEscape)
    document.body.style.overflow = 'hidden'
    
    return () => {
      document.removeEventListener('keydown', handleEscape)
      document.body.style.overflow = 'unset'
    }
  }, [onClose])

  const formatPrice = (price: number | null) => {
    if (!price) return 'Price not available'
    return new Intl.NumberFormat('et-EE', {
      style: 'currency',
      currency: 'EUR',
      maximumFractionDigits: 0,
    }).format(price)
  }

  const formatMileage = (mileage: number | null) => {
    if (!mileage) return 'N/A'
    return `${mileage.toLocaleString()} km`
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

  const details = [
    { label: 'Make', value: listing.make },
    { label: 'Model', value: listing.model },
    { label: 'Year', value: listing.year?.toString() },
    { label: 'Price', value: formatPrice(listing.price) },
    { label: 'Mileage', value: formatMileage(listing.mileage) },
    { label: 'Fuel Type', value: listing.fuel_type },
    { label: 'Transmission', value: listing.transmission },
    { label: 'Body Type', value: listing.body_type },
    { label: 'Color', value: listing.color },
    { label: 'Source', value: getSourceName(listing.source_site) },
  ].filter(item => item.value && item.value !== 'N/A' && item.value !== 'Price not available')

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50 p-4"
      onClick={onClose}
    >
      <div
        className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="sticky top-0 bg-white border-b px-4 sm:px-6 py-4 flex items-start justify-between z-10">
          <div className="flex-1 pr-4">
            <h2 className="text-xl sm:text-2xl font-bold text-gray-900 mb-1">
              {listing.title}
            </h2>
            <div className="flex items-center text-sm text-gray-500">
              <MapPin className="w-4 h-4 mr-1" />
              <span>{getSourceName(listing.source_site)}</span>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors flex-shrink-0"
            aria-label="Close"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* Content */}
        <div className="p-4 sm:p-6">
          {/* Image */}
          {listing.image_url && (
            <div className="mb-6">
              <img
                src={listing.image_url}
                alt={listing.title}
                className="w-full h-auto rounded-lg object-cover max-h-96"
              />
            </div>
          )}

          {/* Price */}
          <div className="mb-6">
            <div className="text-3xl sm:text-4xl font-bold text-primary-600">
              {formatPrice(listing.price)}
            </div>
          </div>

          {/* Details Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-6">
            {details.map((item, index) => (
              <div key={index} className="border-b border-gray-100 pb-3">
                <div className="text-xs sm:text-sm font-medium text-gray-500 uppercase tracking-wide mb-1">
                  {item.label}
                </div>
                <div className="text-sm sm:text-base text-gray-900 font-medium">
                  {item.value}
                </div>
              </div>
            ))}
          </div>

          {/* Description */}
          {listing.description && (
            <div className="mb-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-3">Description</h3>
              <div className="text-sm sm:text-base text-gray-700 whitespace-pre-wrap leading-relaxed">
                {listing.description}
              </div>
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex flex-col sm:flex-row gap-3 pt-4 border-t">
            <a
              href={listing.source_url}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center justify-center gap-2 px-6 py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors font-medium"
            >
              View Original Listing
              <ExternalLink className="w-5 h-5" />
            </a>
            <button
              onClick={onClose}
              className="px-6 py-3 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors font-medium"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

