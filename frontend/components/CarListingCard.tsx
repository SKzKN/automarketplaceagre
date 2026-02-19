'use client'

import { useState } from 'react'
import { CarListing } from '@/types'
import { ExternalLink, MapPin } from 'lucide-react'
import ImageModal from './ImageModal'
import DetailModal from './DetailModal'

interface CarListingCardProps {
  listing: CarListing
}

export default function CarListingCard({ listing }: CarListingCardProps) {
  const [showImageModal, setShowImageModal] = useState(false)
  const [showDetailModal, setShowDetailModal] = useState(false)

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

  return (
    <>
      <div className="bg-white rounded-lg shadow-md overflow-hidden hover:shadow-xl transition-all duration-200 flex flex-col h-full cursor-pointer">
        {listing.image_url && (
          <div 
            className="aspect-video bg-gray-200 overflow-hidden relative cursor-pointer"
            onClick={(e) => {
              e.stopPropagation()
              setShowImageModal(true)
            }}
          >
            <img
              src={listing.image_url}
              alt={listing.title || 'Car listing'}
              className="w-full h-full object-cover hover:scale-105 transition-transform duration-200"
              loading="lazy"
              onError={(e) => {
                e.currentTarget.style.display = 'none'
              }}
            />
            <div className="absolute inset-0 bg-black bg-opacity-0 hover:bg-opacity-10 transition-all duration-200" />
          </div>
        )}
      
      <div className="p-4 sm:p-5 flex flex-col flex-1" onClick={() => setShowDetailModal(true)}>
        <div className="mb-3">
          <h3 className="text-base sm:text-lg font-semibold text-gray-900 line-clamp-2 mb-2 hover:text-primary-600 transition-colors">
            {listing.title}
          </h3>
          
          {listing.make && listing.model && (
            <div className="text-sm text-gray-600 mb-2">
              <span className="font-medium">
                {listing.make}
                {listing.series && <span className="text-gray-500"> {listing.series}</span>}
                {' '}{listing.model}
              </span>
              {listing.year && <span> • {listing.year}</span>}
            </div>
          )}
        </div>

        <div className="mb-4 flex-1">
          <div className="text-xl sm:text-2xl font-bold text-primary-600 mb-3">
            {formatPrice(listing.price)}
          </div>

          <div className="flex flex-wrap gap-x-3 gap-y-1.5 text-xs sm:text-sm text-gray-500">
            {listing.mileage && (
              <span className="flex items-center">
                <span className="font-medium mr-1">Mileage:</span>
                {formatMileage(listing.mileage)}
              </span>
            )}
            {listing.fuel_type && (
              <span>{listing.fuel_type}</span>
            )}
            {listing.transmission && (
              <span>{listing.transmission}</span>
            )}
            {listing.body_type && (
              <span>{listing.body_type}</span>
            )}
          </div>
        </div>

        <div className="flex items-center justify-between pt-4 border-t border-gray-200">
          <div className="flex items-center text-xs sm:text-sm text-gray-500">
            <MapPin className="w-3.5 h-3.5 sm:w-4 sm:h-4 mr-1.5 flex-shrink-0" />
            <span className="truncate">{getSourceName(listing.source_site)}</span>
          </div>
          
          <a
            href={listing.source_url}
            target="_blank"
            rel="noopener noreferrer"
            onClick={(e) => e.stopPropagation()}
            className="flex items-center gap-1.5 px-3 sm:px-4 py-1.5 sm:py-2 text-xs sm:text-sm text-primary-600 hover:text-primary-700 hover:bg-primary-50 font-medium rounded-lg transition-colors"
          >
            <span className="hidden sm:inline">View Original</span>
            <span className="sm:hidden">View</span>
            <ExternalLink className="w-3.5 h-3.5 sm:w-4 sm:h-4 flex-shrink-0" />
          </a>
        </div>
      </div>
      
      {/* Modals */}
      {showImageModal && listing.image_url && (
        <ImageModal
          imageUrl={listing.image_url}
          alt={listing.title || 'Car listing'}
          onClose={() => setShowImageModal(false)}
        />
      )}
      
      {showDetailModal && (
        <DetailModal
          listing={listing}
          onClose={() => setShowDetailModal(false)}
        />
      )}
    </div>
    </>
  )
}

