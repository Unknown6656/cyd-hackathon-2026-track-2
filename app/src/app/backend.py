import json
import textwrap
from typing import NewType

from .agents import classifier_agent, diversion_agent, transaction_agent
from .models import (
    AdviseClassificationRegime,
    AdviseClassificationResponse,
    AdviseTransactionResponse,
    AdviseTransactionVerdict,
    Item,
    Transaction,
)

EKN = NewType("EKN", str)

async def get_classification(item: Item) -> AdviseClassificationResponse:
    item_text = item_to_text(item)
    result = await classifier_agent.run(item_text)
    return result.output

async def is_diversion_risk(user_input: str) -> bool:
    result = await diversion_agent.run(user_input)
    return result.output

async def get_transaction_assessment(
    item: Item,
    transaction: Transaction,
    regime: AdviseClassificationRegime,
) -> AdviseTransactionResponse:
    item_text = item_to_text(item)
    diversion_result = await is_diversion_risk(item_text)
    transaction_result = await transaction_agent.run(transaction.model_dump_json())
    transaction_response = transaction_result.output

    if diversion_result == True:
        transaction_response.verdict = AdviseTransactionVerdict.REFER_TO_AUTHORITY

    return transaction_response

def item_to_text(item: Item) -> str:
    return textwrap.dedent(f'''
    # Item Description
    {item.description}
    
    ## (optional) Item Specification
    ```json
    {json.dumps(item.specifications, indent=2)}
    ```
    ''')