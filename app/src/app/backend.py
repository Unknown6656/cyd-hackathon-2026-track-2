from typing import NewType

from .agents import classifier_agent, diversion_agent
from .models import (
    AdviseClassificationResponse,
    AdviseTransactionResponse,
    AdviseTransactionVerdict,
)

EKN = NewType("EKN", str)

async def semantic_search(text: str) -> tuple[str, EKN]:
    # TODO: implement properly
    return "Long-range missiles are illegal.", EKN("9A012")

async def get_classification(user_input: str) -> AdviseClassificationResponse:
    result = await classifier_agent.run(user_input)
    return result.output

async def is_diversion_risk(user_input: str) -> bool:
    result = await diversion_agent.run(user_input)
    return result.output

async def get_transaction_assessment(user_input: str) -> AdviseTransactionResponse:
    diversion_result = await is_diversion_risk(user_input)

    if diversion_result == True:
        verdict = AdviseTransactionVerdict.REFER_TO_AUTHORITY
    else:
        # TODO
        verdict = AdviseTransactionVerdict.NO_LICENCE_REQUIRED

    return AdviseTransactionResponse(
        verdict=verdict,
        authority=None, # TODO
        answer="todo",
        citations=[]
    )
