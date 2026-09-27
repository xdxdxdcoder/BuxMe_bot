from __future__ import annotations

import re
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(title="Buxme Authentication", docs_url=None, redoc_url=None, openapi_url=None)


class AuthRequest(BaseModel):
    employeeCode: str = Field(min_length=1, max_length=32)
    initData: str = ""


class EmployeeResponse(BaseModel):
    id: str
    code: str
    displayName: str
    maxUserId: int | None = None
    avatarUrl: str | None = None


@app.get("/")
async def healthcheck() -> dict[str, str]:
    return {"status": "ok", "service": "buxme-auth"}


@app.post("/")
@app.post("/api/auth/max")
async def authenticate(request: AuthRequest) -> EmployeeResponse:
    code = request.employeeCode.strip().upper()
    if not re.fullmatch(r"BUX-\d{4}", code):
        raise HTTPException(
            status_code=422,
            detail="Введите код сотрудника в формате BUX-2048",
        )

    return EmployeeResponse(
        id=f"employee-{code.lower()}-{uuid4().hex[:8]}",
        code=code,
        displayName="Менеджер Buxme",
    )
