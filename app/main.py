from fastapi import FastAPI, Request, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

from app.api.evaluation import router as evaluation_router
from app.api.interview import router as interview_router
from app.api.resume import router as resume_router

app = FastAPI()

# Инициализируем роутеры для API
app.include_router(evaluation_router)
app.include_router(interview_router)
app.include_router(resume_router)

# Templates for frontend
templates = Jinja2Templates(directory="app/frontend")

# Роуты для отображения HTML страницы
@app.get("/", response_class=HTMLResponse)
async def index_page(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/select-persona", response_class=HTMLResponse)
async def select_persona_page(request: Request):
    return templates.TemplateResponse("select-candidate.html", {"request": request})

@app.get("/select-profile", response_class=HTMLResponse)
async def select_persona_page(request: Request):
    return templates.TemplateResponse("select-profile.html", {"request": request})

@app.get("/interview", response_class=HTMLResponse)
async def interview_page(request: Request):
    return templates.TemplateResponse("interview.html", {"request": request})

@app.get("/interview_profile", response_class=HTMLResponse)
async def interview_page(request: Request):
    return templates.TemplateResponse("interview_profile.html", {"request": request})

@app.get("/evaluation", response_class=HTMLResponse)
async def evaluation_page(request: Request):
    return templates.TemplateResponse("evaluation.html", {"request": request})

@app.get("/report", response_class=HTMLResponse)
async def report_page(request: Request):
    return templates.TemplateResponse("report.html", {"request": request})

@app.get("/resume-analysis", response_class=HTMLResponse)
async def resume_analysis_page(request: Request):
    return templates.TemplateResponse("resume-analysis.html", {"request": request})
