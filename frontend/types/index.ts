export interface CarListing {
  id: number
  title: string
  make: string | null
  series: string | null
  model: string | null
  make_id: string | null
  series_id: string | null
  model_id: string | null
  year: number | null
  price: number | null
  mileage: number | null
  fuel_type: string | null
  transmission: string | null
  body_type: string | null
  color: string | null
  description: string | null
  image_url: string | null
  source_url: string
  source_site: string
  created_at: string
  updated_at: string
}

// Taxonomy types
export interface MakeDTO {
  id: string
  name: string
  is_top: boolean
}

export interface SeriesDTO {
  id: string
  name: string
  make_id: string
}

export interface ModelDTO {
  id: string
  name: string
  make_id: string
  series_id: string | null
}

export interface Filters {
  makeId: string
  seriesId: string
  modelId: string
  minPrice: string
  maxPrice: string
  minYear: string
  maxYear: string
  bodyType: string
  fuelType: string
  sourceSite: string
}

