import json
import logging
from typing import Iterable, List

from bs4 import BeautifulSoup
from curl_cffi.requests import Session
from curl_cffi.requests.exceptions import HTTPError

from scrapers.repository import ScraperRepository
from .seed_source_taxonomy import (
    SourceTaxonomyExtractor,
    seed_source_taxonomy,
)
from .models import SourceMake, SourceModel, SourceSeries

logger = logging.getLogger(__name__)


class AutodiilerExtractor(SourceTaxonomyExtractor):
    source_site = "autodiiler"

    def __init__(self, session: Session):
        self.session: Session = session

    def _fetch_makes(self) -> list[tuple[str, str]]:
        """Fetches the list of makes from autodiiler and returns list of (make_id, make_label)."""
        makes = []

        try:
            logger.info("Fetching makes from autodiiler...")
            response = self.session.get("https://autodiiler.ee/et")
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            makes_options = soup.select("div#home-search-brand-id-dropdown ul li")

            for make_option in makes_options:
                makes.append(
                    (
                        make_option.attrs["id"].replace("home-search-brand-id-multiselect-option-", "").strip(),
                        make_option.get("aria-label").strip(),
                    )
                )
            return makes
        except HTTPError as e:
            logger.error(f"HTTP error while fetching makes: {e}")
            return []
        except Exception as e:
            logger.error(f"Error fetching makes: {e}")
            return []

    def _fetch_make_tree(self, make_id: int) -> list[dict]:
        try:
            logger.info(f"Fetching (series/models) for make_id {make_id} from autodiiler...")
            response = self.session.get(
                f"https://garage.autodiiler.ee/api/v1/vehicles/misc/brands/{make_id}/models?locale=et&vehicle_type_id="
            )
            response.raise_for_status()

            items = json.loads(response.text)["data"]

            if not isinstance(items, list):
                logger.error(
                    f"Unexpected format for make (series/models) {make_id}: {items}"
                )
                return []
            logger.info(f"Fetched {len(items)} (series/models) for make {make_id}")

            tree = []
            for item in items:
                series_label = item.get("label", None)
                if series_label:
                    result = {
                        "type": "series",
                        "id": None,
                        "label": series_label,
                        "models": [],
                    }
                    for model in item.get("options", []):
                        model_id = model.get("value", None)
                        model_label = model.get("label", "").strip()
                        result["models"].append(
                            {
                                "type": "model_in_series",
                                "id": str(model_id) if model_id is not None else None,
                                "label": model_label,
                            }
                        )
                    tree.append(result)
                else:
                    # standalone model without series
                    for model in item.get("options", []):
                        model_id = model.get("value", None)
                        model_label = model.get("label", "").strip()
                        tree.append(
                            {
                                "type": "model_no_series",
                                "id": str(model_id) if model_id is not None else None,
                                "label": model_label,
                            }
                        )
            return tree
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error while fetching models for make {make_id}: {e}")
            return []
        except HTTPError as e:
            logger.error(f"HTTP error while fetching models for make {make_id}: {e}")
            return []
        except Exception as e:
            logger.error(f"Error fetching models for make {make_id}: {e}")
            return []

    def iter_makes(self) -> Iterable[SourceMake]:
        makes = self._fetch_makes() 
        for index, mk in enumerate(makes, start=1):
            logger.info(f"[{index}/{len(makes)}] Processing make: {mk[1]}")
            make_id = mk[0]
            make_label = mk[1]

            series_nodes = self._fetch_make_tree(make_id)

            series_list: List[SourceSeries] = []
            models_no_series: List[SourceModel] = []

            for node in series_nodes:
                if node["type"] == "series":
                    series_list.append(
                        SourceSeries(
                            source_series_id=node["id"],
                            label=node["label"],
                            models=[
                                SourceModel(
                                    source_model_id=str(m["id"]), label=m["label"]
                                )
                                for m in node.get("models", [])
                            ],
                        )
                    )
                else:
                    models_no_series.append(
                        SourceModel(source_model_id=str(node["id"]), label=node["label"])
                    )

            yield SourceMake(
                source_make_id=make_id,
                label=make_label,
                series=series_list,
                models_no_series=models_no_series,
            )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    session = Session(impersonate="chrome")
    extractor = AutodiilerExtractor(session=session)

    repo = ScraperRepository()
    repo.connect()

    seed_source_taxonomy(repo, extractor)
