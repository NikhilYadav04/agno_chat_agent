from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.routes import query_route, history_route, maintenance_route

app = FastAPI(
    title="PillBin Agent API",
    description="FastAPI backend for the PillBin medical agent with streaming, RAG, and memory management.",
    version="1.0.0",
)

# ── CORS (adjust origins for production) ──
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ──
app.include_router(query_route.router, tags=["Query"])
app.include_router(history_route.router, tags=["History"])
app.include_router(maintenance_route.router, tags=["Maintenance"])


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
