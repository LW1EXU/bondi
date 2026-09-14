from datetime import datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class RawBranch(StrictModel):
    line_id: str
    name: str
    direction: Literal[0, 1]
    variant: str = "regular"
    stop_names: list[str]
    evidence: str = Field(min_length=10)
    schedule_text: str | None = None


class RawAlert(StrictModel):
    title: str
    description: str
    line_ids: list[str]
    evidence: str = Field(min_length=10)
    starts_at: datetime | None = None
    ends_at: datetime | None = None


class Extraction(StrictModel):
    branches: list[RawBranch]
    alerts: list[RawAlert]


class Address(StrictModel):
    original: str
    canonical: str
    kind: Literal["intersection", "poi", "unknown"]


class Addresses(StrictModel):
    addresses: list[Address]


class GazetteerEntry(StrictModel):
    canonical: str
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)
    source_url: str = Field(min_length=8)


class Stop(GazetteerEntry):
    id: str


class Branch(StrictModel):
    id: str
    line_id: str
    name: str
    direction: Literal[0, 1]
    variant: str
    stops: list[Stop]
    unresolved: list[str]
    source_url: str
    source_sha256: str
    evidence: str
    schedule_text: str | None = None


class Dataset(StrictModel):
    branches: list[Branch]


class Review(StrictModel):
    approved: bool
    issues: list[str]
