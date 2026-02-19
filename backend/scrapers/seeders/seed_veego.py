from __future__ import annotations

import json
import logging
import re
from typing import Dict, Iterable, List

from curl_cffi.requests import Session
from curl_cffi.requests.exceptions import HTTPError

from scrapers.repository import ScraperRepository

from .models import SourceMake, SourceModel, SourceSeries
from .seed_source_taxonomy import SourceTaxonomyExtractor, seed_source_taxonomy

logger = logging.getLogger(__name__)

class VeegoTranslator:
    # Matches entries like:
    # series:{t:0,b:{t:2,i:[{t:3}],s:"seeria"}}
    # "1 series":{t:0,b:{t:2,i:[{t:3}],s:"1 seeria"}}
    _ENTRY_RE = re.compile(
        r'(?:^|,)(?:"((?:\\.|[^"\\])*)"|([A-Za-z_$][\w$]*)):\{t:0,b:\{t:2,i:\[\{t:3\}\],s:"((?:\\.|[^"\\])*)"\}\}'
    )

    def __init__(self, mapping: Dict[str, str]):
        self.mapping = mapping

    @classmethod
    def from_js_string(cls, js_string: str) -> "VeegoTranslator":
        mapping: Dict[str, str] = {}
        for m in cls._ENTRY_RE.finditer(js_string):
            key = m.group(1) or m.group(2)  # quoted key or bare identifier key
            val = m.group(3)
            mapping[key] = val

        if not mapping:
            raise ValueError("No translations found. Pattern may have changed in the Nuxt chunk.")

        return cls(mapping)

    def t(self, text: str, *, no_translate: bool = False) -> str:
        """
        Translate a label. If `no_translate=True`, returns input unchanged.
        Strategy:
          1) Exact dictionary match
          2) Special-case 'series' with number in either order
          3) Fallback: replace standalone word 'series' if we know its translation
        """
        if no_translate:
            return text

        # 1) exact hit
        direct = self.mapping.get(text)
        if direct is not None:
            return direct

        # 2) normalize “1 series” or “series 1”
        series_et = self.mapping.get("series")
        if series_et:
            m1 = re.fullmatch(r"\s*(\d+)\s+series\s*", text, flags=re.IGNORECASE)
            if m1:
                return f"{m1.group(1)} {series_et}"

            m2 = re.fullmatch(r"\s*series\s+(\d+)\s*", text, flags=re.IGNORECASE)
            if m2:
                return f"{series_et} {m2.group(1)}"

            # 3) replace word boundary series -> seeria
            replaced = re.sub(r"\bseries\b", series_et, text, flags=re.IGNORECASE)
            if replaced != text:
                return replaced

        # no translation known
        return text


class VeegoExtractor(SourceTaxonomyExtractor):
    source_site = "veego"

    def __init__(self, session: Session, translator: VeegoTranslator):
        self.session: Session = session
        self.translator: VeegoTranslator = translator

    def _fetch_makes(self) -> list[tuple[str, str]]:
        """Fetches the list of makes from Veego and returns list of (make_id, make_label)."""
        makes = []
        try:
            response = self.session.get("https://api.veego.ee/api/attr/vehicles/makes?top=false&all=true")
            response.raise_for_status()
            makes = response.json()

            if not isinstance(makes, list):
                return []
            
            for make in makes:
                makes.append((str(make.get("id")), make.get("name", "")))
            return makes
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error while fetching makes: {e}")
            return []
        except HTTPError as e:
            logger.error(f"HTTP error while fetching makes: {e}")
            return []
        except Exception:
            return []
        
    def _fetch_make_tree(self, make_id: str) -> list[dict]:
        try:
            logger.info(f"Fetching make tree for make_id {make_id} from Veego...")
            response = self.session.get(f"https://api.veego.ee/api/attr/{make_id}/models")
            response.raise_for_status()
            items = response.json()
            if not isinstance(items, list):
                return []
            
            tree = []
            for item in items:
                if item["lvl"] == 1:
                    if len(item.get("models", [])) != 0:
                        result = {}
                        result["type"] = "series"
                        result["models"] = []
                        result["label"] = self.translator.t(item["name"])
                        result["id"] = str(item["id"])
                        for model in item.get("models", []):
                            result["models"].append(
                                {
                                    "type": "model_in_series",
                                    "label": self.translator.t(model["name"]),
                                    "id": str(model["id"])
                                }
                            )
                        tree.append(result)
                    else:
                        tree.append(
                            {
                                "type": "model_no_series",
                                "label": self.translator.t(item["name"]),
                                "id": str(item["id"])
                            }
                        )

            return tree
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error while fetching models for make {make_id}: {e}")
            return []
        except HTTPError as e:
            logger.error(f"HTTP error while fetching models for make {make_id}: {e}")
            return []
        except Exception:
            return []

    def iter_makes(self) -> Iterable[SourceMake]:
        makes = self._fetch_makes()  # [(make_id, make_label), ...]
        logger.info(f"Found {len(makes)} makes in Veego taxonomy.")
        for index, mk in enumerate(makes, start = 1):
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
                            source_series_id=str(node["id"]),
                            label=node["label"],
                            models=[
                                SourceModel(source_model_id=str(m["id"]), label=m["label"])
                                for m in node.get("models", [])
                            ],
                        )
                    )
                else:
                    models_no_series.append(
                        SourceModel(
                            source_model_id=str(node["id"]), 
                            label=node["label"]
                        )
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
    page = session.get("https://veego.ee/_nuxt/D7p4OLQY.js")
    translator = VeegoTranslator.from_js_string(js_string=page.text)
    extractor = VeegoExtractor(session=session, translator=translator)

    repo = ScraperRepository()
    repo.connect()  

    seed_source_taxonomy(repo, extractor)
