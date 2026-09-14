from typing import Any
from enum import Enum
from pydantic import BaseModel


class Item(BaseModel):
    description: str | None = None
    specifications: dict[str, Any] | None = None # Free-form: any keys, any units, no guarantee a given parameter is present.

class Transaction(BaseModel):
    consignee: str | None = None
    end_user: str | None = None
    intermediaries: list[str] | None = None
    destination: str | None = None
    stated_end_use: str | None = None
    routing: list[str] | None = None
    value_chf: float | None = None

class Document(BaseModel):
    type: str | None = None
    text: str

class AdviseRequest(BaseModel):
    """At least one block is present. query / item / transaction appear at most
    once; documents is a list. When several are present they are related: the
    item is the product in the transaction and the query is scoped to both."""
    query: str | None = None
    item: Item | None = None
    transaction: Transaction | None = None
    documents: list[Document] | None = None

class AdviseQueryResponse(BaseModel):
    answer: str
    citations: list[str]

class AdviseClassificationRegime(str, Enum):
    WAR_MATERIEL = "war_materiel"
    SPECIFIC_MILITARY = "specific_military"
    DUAL_USE = "dual_use"
    NONE = "none"

class AdviseClassificationResponse(BaseModel):
    controlled: bool
    regime: AdviseClassificationRegime
    entries: list[str]
    deciding_text: str
    citations: list[str]

class AdviseTransactionVerdict(str, Enum):
    NO_LICENCE_REQUIRED = "NO_LICENCE_REQUIRED"
    LICENCE_REQUIRED = "LICENCE_REQUIRED"
    PROHIBITED = "PROHIBITED"
    REFER_TO_AUTHORITY = "REFER_TO_AUTHORITY"

class AdviseTransactionResponse(BaseModel):
    verdict: AdviseTransactionVerdict
    authority: str | None = None
    answer: str
    citations: list[str]

class AdviseResponse(BaseModel):
    refer_to_authority: bool
    query: AdviseQueryResponse | None = None
    classification: AdviseClassificationResponse | None = None
    transaction: AdviseTransactionResponse | None = None
