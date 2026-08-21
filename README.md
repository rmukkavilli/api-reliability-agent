# Agentic API Reliability Checker

A read-only API reliability demo that combines LLM-driven tool selection with deterministic Python validation. The project uses the OpenAI Agents SDK with a Gemini model exposed through an OpenAI-compatible client.

The current demo checks a deployed FastAPI clinical-screening service at three levels:

- `GET /health` for service availability
- `GET /patients` for the Patient collection contract
- `GET /screenings` for the Screening collection contract

The agent never creates, updates, or deletes API data.

## What this project demonstrates

| Capability | Implementation |
| --- | --- |
| Prompt engineering | Agent instructions define evidence, safety, completion, and reporting rules. |
| Tool calling | `@function_tool` exposes Python checks to the agent. |
| Agent orchestration | A targeted agent and a complete-check agent coordinate registered tools. |
| Async API integration | Tools use `httpx.AsyncClient` and `await`; the agent runs through `Runner.run`. |
| Deterministic validation | Python validates status codes, JSON parsing, response types, and record counts. |
| Safety constraints | Only explicitly registered, read-only `GET` tools are available. |

This is currently multi-tool orchestration. Automatic handoffs or routing between the two agents are planned, not yet implemented.

## How it works

1. The CLI sends the target base URL to `complete_api_reliability_agent`.
2. Agent instructions require every registered read-only tool to run.
3. Each tool sends an asynchronous HTTP request to its endpoint.
4. Python validates the response and returns evidence to the agent.
5. The agent combines the tool evidence into a final reliability report.

The model explains the result, but Python owns the pass/fail conditions for the Patient and Screening collection checks.

## Current validation contracts

| Endpoint | Passing evidence |
| --- | --- |
| `/health` | Endpoint responds and its HTTP status/body are returned as evidence. |
| `/patients` | HTTP `200`, valid JSON, and a JSON-list response. |
| `/screenings` | HTTP `200`, valid JSON, and a JSON-list response. |

An empty collection such as `[]` is valid. It means the endpoint contract passed with zero records; it does not mean the API is unhealthy.

Patient and Screening tools report only response structure and record count. They do not include record values in the agent report.

## Project structure

```text
api-reliability-agent/
|-- app/
|   |-- agent.py
|   `-- tools.py
|-- demo.py
|-- README.md
`-- requirements.txt
```

## Setup

### 1. Create and activate a virtual environment

PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 2. Install dependencies

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Configure the model API key

The current agent configuration reads `GEMINI_API_KEY` from the environment:

```powershell
$env:GEMINI_API_KEY="your-api-key"
```

Do not commit API keys or local environment files.

## Run the demo

```powershell
python demo.py --target https://backend-project-api-cswq.onrender.com
```

The complete agent automatically calls every registered read-only reliability tool. The CLI prompt does not need to list individual endpoints.

Example, with record values omitted:

```text
API Reliability Check Report

/health      200  PASSED
/patients    200  JSON list  1 record   PASSED
/screenings  200  JSON list  0 records  PASSED

Conclusion: all registered read-only checks passed.
```

Actual record counts depend on the target database.

## Agent roles

### API Reliability Agent

`api_reliability_agent` supports targeted investigation using the relevant registered tool.

### Complete API Reliability Agent

`complete_api_reliability_agent` must call every registered tool before producing its conclusion.

Both agents share the same explicit tool allowlist:

```python
tools=[
    check_api_health,
    check_screening_api,
    check_patient_api,
]
```

Adding a Python function to `tools.py` does not expose it automatically. It must be deliberately registered in an agent's `tools` list.

## Safety model

- Tools issue only `GET` requests.
- No POST, PUT, PATCH, or DELETE capability is registered.
- Network failures and malformed JSON are returned as evidence instead of crashing the agent workflow.
- Patient record values are not included in reliability reports.
- Requests use a finite timeout.
- The demo accepts only absolute `http://` or `https://` target URLs.

This is foundational safety, not a complete production security boundary. The roadmap includes an approved-host policy and formal guardrails.

## Roadmap

- Validate that `/health` contains an expected healthy status value, not only a successful response.
- Discover safe `GET` routes from `/openapi.json`.
- Support parameterized routes using controlled, non-sensitive test records.
- Add latency measurement and configurable thresholds.
- Add retry policies and failure classification.
- Return a structured report schema instead of relying on free-form summarization.
- Add unit tests with mocked HTTP responses and agent-behavior evaluations.
- Add CI execution and saved demo artifacts.
- Add an approved-host policy, authentication handling, and secret redaction.
- Add deterministic routing or SDK handoffs between specialist agents.

## Technology

- Python
- OpenAI Agents SDK
- OpenAI-compatible asynchronous model client
- Gemini
- HTTPX
- FastAPI/OpenAPI target service

## Reference

- [OpenAI Agents SDK guide](https://developers.openai.com/api/docs/guides/agents)
- [OpenAI Agents SDK quickstart](https://developers.openai.com/api/docs/guides/agents/quickstart)
- [Using tools](https://developers.openai.com/api/docs/guides/tools)
