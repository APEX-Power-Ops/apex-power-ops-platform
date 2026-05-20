"""
FastAPI application entry point for the mutation seam.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import (
    apparatus,
    assignments,
    checklist,
    customer_completion,
    temp_power_customer_delivery_events,
    temp_power_customer_delivery_proof_reviews,
    durable_field_records,
    financial_handoff,
    health,
    hours,
    issues,
    production_tracking,
    project_import_approvals,
    project_import_contract_support,
    project_imports,
    project_import_task_plans,
    reads,
    schedule,
    snapshots,
    tasks,
    temp_power_actuals_capture_reviews,
    temp_power_customer_preview_reviews,
    workpackages,
)

app = FastAPI(
    title=settings.SERVICE_NAME,
    version=settings.VERSION,
    description="Governed mutation seam for APEX Platform PM/work domain",
)

# ===== CORS Middleware =====
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_CREDENTIALS,
    allow_methods=settings.CORS_METHODS,
    allow_headers=settings.CORS_HEADERS,
)

# ===== Include Routers =====
app.include_router(health.router)
app.include_router(apparatus.router)
app.include_router(assignments.router)
app.include_router(checklist.router)
app.include_router(customer_completion.router)
app.include_router(temp_power_customer_delivery_events.router)
app.include_router(temp_power_customer_delivery_proof_reviews.router)
app.include_router(durable_field_records.router)
app.include_router(financial_handoff.router)
app.include_router(hours.router)
app.include_router(issues.router)
app.include_router(production_tracking.router)
app.include_router(project_import_approvals.router)
app.include_router(project_import_contract_support.router)
app.include_router(project_imports.router)
app.include_router(project_import_task_plans.router)
app.include_router(temp_power_actuals_capture_reviews.router)
app.include_router(temp_power_customer_preview_reviews.router)
app.include_router(tasks.router)
app.include_router(workpackages.router)
app.include_router(snapshots.router)
app.include_router(reads.router)
app.include_router(schedule.router)  # UI-002a read-only P6 schedule bridge


# ===== Root Endpoint =====
@app.get("/")
async def root():
    return {
        "service": "apex-mutation-seam",
        "version": settings.VERSION,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.PORT,
        reload=True,
    )
