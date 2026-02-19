import logging
from scrapers.repository import ScraperRepository, norm_label

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# List of top brands to mark (normalized labels will be used for matching)
TOP_BRANDS = [
    # Japanese
    "Toyota",
    "Honda",
    "Nissan",
    "Mazda",
    "Subaru",
    "Mitsubishi",
    "Suzuki",
    # German
    "Volkswagen",
    "VW",
    "BMW",
    "Mercedes-Benz",
    "Mercedes",
    "Audi",
    "Porsche",
    "Opel",
    # American
    "Ford",
    "Chevrolet",
    "GMC",
    "Cadillac",
    "Tesla",
    "Jeep",
    "Dodge",
    "Chrysler",
    "Ram",
    # Korean
    "Hyundai",
    "Kia",
    "Genesis",
    # French
    "Renault",
    "Peugeot",
    "Citroën",
    "Citroen",
    # Italian
    "Fiat",
    "Alfa Romeo",
    "Ferrari",
    "Lamborghini",
    "Maserati",
    # British
    "Jaguar",
    "Land Rover",
    "Range Rover",
    "Mini",
    "Rolls-Royce",
    "Rolls Royce",
    "Bentley",
    "Aston Martin",
    # Swedish
    "Volvo",
    "Polestar",
    # Chinese
    "BYD",
]


def main():
    """Mark top brands in the database."""
    repo = ScraperRepository()
    repo.connect()
    
    # Normalize brand names for matching
    top_brands_normalized = {norm_label(brand) for brand in TOP_BRANDS}
    
    logger.info(f"Looking for {len(top_brands_normalized)} unique top brand patterns...")
    
    # First, reset all is_top flags to False
    reset_result = repo.makes.update_many(
        {},
        {"$set": {"is_top": False}}
    )
    logger.info(f"Reset is_top flag for {reset_result.modified_count} makes")
    
    # Find and update matching brands
    updated_count = 0
    matched_brands = []
    
    # Get all makes and check against normalized top brands
    all_makes = list(repo.makes.find({}))
    logger.info(f"Found {len(all_makes)} total makes in database")
    
    for make in all_makes:
        make_norm = make.get("norm", "")
        make_name = make.get("name_et", "")
        
        # Check if this make matches any of our top brands
        if make_norm in top_brands_normalized:
            result = repo.makes.update_one(
                {"_id": make["_id"]},
                {"$set": {"is_top": True}}
            )
            if result.modified_count > 0:
                updated_count += 1
                matched_brands.append(make_name)
    
    logger.info(f"Marked {updated_count} brands as top brands:")
    for brand in sorted(matched_brands):
        logger.info(f"  ✓ {brand}")
    
    # Log any top brands that weren't found
    found_norms = {norm_label(brand) for brand in matched_brands}
    missing = top_brands_normalized - found_norms
    if missing:
        logger.warning("Some top brands were not found in database:")
        for brand in sorted(missing):
            logger.warning(f"  ✗ {brand}")
    
    repo.disconnect()
    logger.info("Done!")


if __name__ == "__main__":
    main()
