from app.agents import calculation_agent, config


def test_calculation_agent_replies() -> None:
    result = calculation_agent.run_sync("What is 12.5% of 480?")

    print(f"Using model '{config.model}' at '{config.openai_base_url}'")
    print(result.output)
    assert result.output.strip()
