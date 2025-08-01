from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum


class Decision(str, Enum):
    STRONG_COP = "strong_cop"
    COP = "cop"
    MAYBE = "maybe"
    PASS = "pass"


class ParsedItem(BaseModel):
    title: str
    brand: Optional[str] = None
    size: Optional[str] = None
    color: Optional[str] = None
    gender: Optional[str] = None
    price: float
    currency: str
    notes: List[str] = Field(default_factory=list)


class MarketComparable(BaseModel):
    source: str
    title: str
    price: float
    currency: str
    condition: Optional[str] = None
    fee_adjusted_price: Optional[float] = None
    url: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class MarketStats(BaseModel):
    market_median: Optional[float] = None
    adjusted_market_price: Optional[float] = None
    user_price_vs_median_delta: Optional[float] = None
    sample_size: int = 0


class DecisionResult(BaseModel):
    verdict: str
    confidence: float = Field(ge=0.0, le=1.0)
    reasons: List[str] = Field(default_factory=list)


class EvaluationRequest(BaseModel):
    raw_tag: str
    overrides: Optional[Dict[str, Any]] = Field(default_factory=dict)


class EvaluationResponse(BaseModel):
    parsed: ParsedItem
    converted_price_usd: float
    market_comparables: List[MarketComparable]
    stats: MarketStats
    decision: DecisionResult