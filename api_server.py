from __future__ import annotations

import json
from typing import Any, Iterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field

from analysis_pipeline import run_web_analysis, stream_web_analysis


app = FastAPI(title="Executive Board API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AnalyzeRequest(BaseModel):
    problem: str = Field(..., min_length=1)
    save_to_memory: bool = True


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/analyze")
def analyze(req: AnalyzeRequest) -> Any:
    data = run_web_analysis(req.problem, save_to_memory=req.save_to_memory)
    return JSONResponse(content=data)


def _ndjson_stream(problem: str, save_to_memory: bool) -> Iterator[bytes]:
    for item in stream_web_analysis(problem, save_to_memory=save_to_memory):
        yield (json.dumps(item, ensure_ascii=False) + "\n").encode("utf-8")


@app.post("/stream")
def stream(req: AnalyzeRequest) -> StreamingResponse:
    return StreamingResponse(
        _ndjson_stream(req.problem, req.save_to_memory),
        media_type="application/x-ndjson; charset=utf-8",
        headers={"Cache-Control": "no-cache"},
    )

