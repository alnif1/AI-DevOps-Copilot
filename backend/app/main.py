
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.analyzer import analyze_logs
from app.schemas import AnalyzeRequest, IncidentReport

app = FastAPI(
    title="AI DevOps Copilot",
    description="Analyze application logs and investigate incidents.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "ai-devops-copilot"}


@app.post("/api/v1/analyze", response_model=IncidentReport)
def analyze_incident(request: AnalyzeRequest) -> IncidentReport:
    return analyze_logs(
        log_text=request.log_text,
        service_name=request.service_name,
        environment=request.environment,
    )
