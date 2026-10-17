
from contextlib import asynccontextmanager
from uuid import UUID

from fastapi import FastAPI, HTTPException, Response, status
from fastapi.middleware.cors import CORSMiddleware

from app.analyzer import analyze_logs
from app.database import (
    create_incident,
    delete_all_incidents,
    delete_incident,
    get_connection,
    initialize_database,
    list_incidents,
)
from app.schemas import AnalyzeRequest, IncidentHistoryItem, IncidentReport


@asynccontextmanager
async def lifespan(_: FastAPI):
    initialize_database()
    yield


app = FastAPI(
    title="AI DevOps Copilot",
    description="Analyze application logs and investigate incidents.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=False,
    allow_methods=["DELETE", "GET", "POST"],
    allow_headers=["Content-Type"],
)


@app.get("/health")
def health_check():
    with get_connection() as connection:
        connection.execute("SELECT 1")
    return {"status": "healthy", "service": "ai-devops-copilot"}


@app.post("/api/v1/analyze", response_model=IncidentReport)
def analyze_incident(request: AnalyzeRequest) -> IncidentReport:
    report = analyze_logs(
        log_text=request.log_text,
        service_name=request.service_name,
        environment=request.environment,
    )
    create_incident(
        logs=request.log_text,
        report=report.model_dump(mode="json"),
    )
    return report


@app.get("/api/v1/history", response_model=list[IncidentHistoryItem])
def get_incident_history() -> list[IncidentHistoryItem]:
    return [
        IncidentHistoryItem.model_validate(item)
        for item in list_incidents()
    ]


@app.delete(
    "/api/v1/history",
    status_code=status.HTTP_204_NO_CONTENT,
)
def clear_incident_history() -> Response:
    delete_all_incidents()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.delete(
    "/api/v1/history/{incident_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_incident(incident_id: UUID) -> Response:
    if not delete_incident(incident_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found.")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
