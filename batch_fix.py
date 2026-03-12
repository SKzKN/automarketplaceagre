import logging
from repository import ScraperRepository
from resolver import resolve_one_listing

logging.basicConfig(level=logging.INFO)
repo = ScraperRepository()
repo.connect()

query = {"$or": [{"make_id": {"$exists": False}}, {"make_id": None}]}
total = repo.car_listings.count_documents(query)
print(f'Found {total} listings needing resolution')

if total == 0:
    print('All listings already resolved!')
    exit(0)

processed = 0
updated = 0
skipped = 0
batch_size = 1000
skip = 0

while True:
    listings = list(repo.car_listings.find(query).skip(skip).limit(batch_size))
    if not listings:
        break

    print(f'Processing batch starting at {skip} ({processed}/{total})')

    for listing in listings:
        ids = resolve_one_listing(repo, listing)
        if ids['make_id']:
            repo.car_listings.update_one(
                {'_id': listing['_id']},
                {'$set': {'make_id': ids['make_id'], 'series_id': ids['series_id'], 'model_id': ids['model_id']}}
            )
            updated += 1
        else:
            skipped += 1
        processed += 1

    skip += batch_size

print(f'Done! Updated: {updated}, Skipped (no make mapping): {skipped}, Total processed: {processed}')
