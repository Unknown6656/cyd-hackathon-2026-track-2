from typing import NewType

from .agents import classifier_agent

EKN = NewType("EKN", str)

async def semantic_search(text: str) -> tuple[str, EKN]:
    # TODO: implement properly
    return "Long-range missiles are illegal.", EKN("9A012")

async def get_classification(user_input: str) -> str:
    result = await classifier_agent.run(user_input)
    return result.output