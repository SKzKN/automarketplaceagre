import logging
from typing import Any, Dict, Iterable, List, Optional, Tuple

from bs4 import BeautifulSoup
from curl_cffi.requests import Session
from curl_cffi.requests.exceptions import HTTPError

from scrapers.repository import ScraperRepository

from .models import SourceMake, SourceModel, SourceSeries
from .seed_source_taxonomy import SourceTaxonomyExtractor, seed_source_taxonomy

logger = logging.getLogger(__name__)


class Auto24TaxonomyExtractor(SourceTaxonomyExtractor):
    source_site = "auto24"

    def __init__(self, session: Session):
        self.session: Session = session

    def _fetch_makes(self) -> List[Tuple[str, str]]:
        """Fetches the list of makes from auto24 and returns list of (make_id, make_label)."""
        makes = []

        try:
            logger.info("Fetching makes from auto24...")
            response = self.session.get("https://www.auto24.ee/")
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            makes_options = soup.select("select#searchParam-cmm-2-make option")

            for option in makes_options:
                make_id = option.get("value")
                make_label = option.get_text(strip=True)
                if make_id and make_label:
                    makes.append((make_id, make_label))
            logger.info(f"Fetched {len(makes)} makes from auto24.")
            return makes
        except HTTPError as e:
            logger.error(f"HTTP error while fetching makes: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error while fetching makes: {e}")
            return []

    def _fetch_make_tree(self, make_id: str) -> List[Dict[str, Any]]:
        """Fetches the series/model tree for a given make from auto24."""
        try:
            logger.info(f"Fetching make tree for make_id {make_id} from auto24...")
            response = self.session.get(
                url=f"https://www.auto24.ee/services/data_json.php?q=models&existonly=true&parent={make_id}&type=100"
            )
            response.raise_for_status()
            json_payload = response.json()
            tree = ((json_payload or {}).get("q") or {}).get("response") or []
            if not isinstance(tree, list):
                raise ValueError("auto24 make tree: expected q.response list")
            logger.info(
                f"Fetched make tree for make_id {make_id} with {len(tree)} nodes."
            )
            return tree
        except HTTPError as e:
            logger.error(
                f"HTTP error while fetching make tree for make_id {make_id}: {e}"
            )
            return []
        except ValueError as e:
            logger.error(
                f"Value error while parsing make tree for make_id {make_id}: {e}"
            )
            return []
        except Exception as e:
            logger.error(
                f"Unexpected error while fetching make tree for make_id {make_id}: {e}"
            )
            return []

    def _iter_series_and_models(
        tree: List[Dict[str, Any]],
    ) -> Iterable[Tuple[Dict[str, Any], Optional[List[Dict[str, Any]]]]]:
        """
        Iterates over the auto24 tree and yields tuples of (node, children).
        Nodes with children are series; nodes without children are standalone models.
        """
        for node in tree:
            children = node.get("children")
            if isinstance(children, list) and children:
                # This is a series with child models
                yield node, children
            else:
                # This is a standalone model without series
                yield node, None

    def iter_makes(self) -> Iterable[SourceMake]:
        makes = self._fetch_makes()
        for make_id, make_name in makes:
            make_tree = self._fetch_make_tree(make_id)

            series_list = []
            models_no_series = []

            for series_node, children in self._iter_series_and_models(make_tree):
                series_label_raw = series_node.get("label") or ""
                series_value = series_node.get("value")

                if not children:
                    # This is a model without series
                    models_no_series.append(
                        SourceModel(
                            source_model_id=str(series_value)
                            if series_value is not None
                            else None,
                            label=series_label_raw,
                        )
                    )
                    continue

                # This is a normal series with children models
                models = []
                for child in children:
                    model_label_raw = child.get("label") or ""
                    model_value = child.get("value")
                    models.append(
                        SourceModel(
                            source_model_id=str(model_value)
                            if model_value is not None
                            else None,
                            label=model_label_raw,
                        )
                    )
                series_list.append(
                    SourceSeries(
                        source_series_id=str(series_value)
                        if series_value is not None
                        else None,
                        label=series_label_raw,
                        models=models,
                    )
                )
            yield SourceMake(
                source_make_id=make_id,
                label=make_name,
                series=series_list,
                models_no_series=models_no_series,
            )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    session = Session(impersonate="chrome")
    extractor = Auto24TaxonomyExtractor(session)

    repo = ScraperRepository()
    repo.connect()

    seed_source_taxonomy(repo, extractor)
