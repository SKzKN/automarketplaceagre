from pydantic import BaseModel

class SourceMake(BaseModel):
     source_make_id: str | None  # id on source (if exists)
     label: str # "BMW"
     series: list["SourceSeries"] # series may be absent for some makes/sources 
     models_no_series: list["SourceModel"] # some sources might have models directly under make (no series)

class SourceSeries(BaseModel):
    source_series_id: str | None
    label: str # "e.g. 1 seeria"
    models: list["SourceModel"]

class SourceModel(BaseModel):
    source_model_id: str | None
    label: str # "e.g. 116"