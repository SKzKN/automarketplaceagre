from typing import Optional

from pydantic import BaseModel


class MakeDTO(BaseModel):
    id: str
    name: str
    is_top: bool = False


class SeriesDTO(BaseModel):
    id: str
    name: str
    make_id: str


class ModelDTO(BaseModel):
    id: str
    name: str
    make_id: str
    series_id: Optional[str] = None
