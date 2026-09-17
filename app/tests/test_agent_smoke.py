import json
from app.agents import classifier_agent, config
from app.models import AdviseClassificationRegime


def test_agent_replies() -> None:
    item: dict = {
        "description": "standalone high-speed ADC integrated circuit for test and measurement",
        "specifications": {
            "resolution_bits": 12,
            "sampling_rate": "450 MSa/s",
            "channels": 1
        }
    }
    item_text = json.dumps(item)

    result = classifier_agent.run_sync(
        item_text
        #"Is an export license needed for headphones? A0001: Headphones never require an export license.",
        #usage_limits=UsageLimits(request_limit=5, tool_calls_limit=3),
    )

    print(f"Using model '{config.model}' at '{config.openai_base_url}'")
    print("RESULT: ", result.output)
    assert result.output
    assert result.output.regime == AdviseClassificationRegime.DUAL_USE
