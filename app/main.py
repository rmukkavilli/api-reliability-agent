from agents import Runner
from fastapi import FastAPI

from app.agent import api_reliability_agent
from app.schemas import AgentRunRequest

app = FastAPI(
    title="API Reliability Agent",
    version="0.1.0",
)


@app.get("/health")
def health():
    return {"status": "healthy"}

@app.post("/agent/run")
async def run_agent(request: AgentRunRequest):
    agent_input = (
        f"Target API: {request.target_url}\n"
        f"Question: {request.question}"
    )

    return {
        "target_url": str(request.target_url),
        "question": request.question,
        "agent_input": agent_input,
        "status": "received",
    }