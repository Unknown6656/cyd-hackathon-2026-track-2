from app.agents import classifier_agent, config


def test_agent_replies() -> None:
    result = classifier_agent.run_sync("Is an export license needed for headphones? A0001: Headphones never require an export license.")

    print(f"Using model '{config.model}' at '{config.openai_base_url}'")
    print(result.output)
    assert result.output.strip()
