from fastapi import APIRouter, Request

from app.agents.evaluation_agent import create_evaluation_agent

from agents import Runner

from app.agents.prompts.utils import load_prompts

router = APIRouter()

prompts = load_prompts("evaluation_system_prompt.yaml")
system_prompt = prompts["evaluation_system_prompt"]

# Хранилище для последних результатов оценки
last_evaluation_result = {
    "Situation": "-",
    "Task": "-", 
    "Action": "-",
    "Result": "-"
}

@router.post("/api/evaluation")
async def evaluate_endpoint(request: Request):
    global last_evaluation_result
    
    data = await request.json()
    messages = data.get("messages")
    agent = create_evaluation_agent(system_prompt)
    response = await Runner.run(agent, messages)
    last_evaluation_result = response.final_output_as(cls=dict)
    

@router.get("/api/evaluation")
async def get_evaluation_result():
    """Эндпоинт для получения последних результатов оценки."""
    return last_evaluation_result