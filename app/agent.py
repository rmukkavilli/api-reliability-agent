import os
from app.tools import check_api_health, check_screening_api, check_patient_api

from agents import Agent, OpenAIChatCompletionsModel, set_tracing_disabled
from openai import AsyncOpenAI

gemini_client = AsyncOpenAI(
    api_key=os.environ["GEMINI_API_KEY"],
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
)

gemini_model = OpenAIChatCompletionsModel(
    model="gemini-3.6-flash",
    openai_client=gemini_client,
)

set_tracing_disabled(True)
api_reliability_agent = Agent(
    name="API Reliability Agent",
    model=gemini_model,
    instructions="""
    You are an API reliability agent.

    Use the available read-only tools to investigate the target API.

    When asked whether an API is healthy:
    - Call the health-check tool.
    - Base your conclusion only on evidence returned by the tool.
    - Report the endpoint, HTTP status, and response details.
    - Clearly explain failures or unavailable endpoints.
    - Never claim that something was verified if no tool confirmed it.
    - Never make destructive or data-modifying requests.
    """,
    tools=[check_api_health, check_screening_api, check_patient_api],
)

complete_api_reliability_agent = Agent(
    name="Complete API Reliability Agent",
    model=gemini_model,
    instructions="""
    You perform complete read-only API reliability checks.

    Always call every registered tool before giving a conclusion.
    Do not claim the API is fully healthy unless every check passes.
    Clearly report any failed, incomplete, or unavailable check.
    """,
    tools=[
        check_api_health,
        check_screening_api,
        check_patient_api,
    ],
)