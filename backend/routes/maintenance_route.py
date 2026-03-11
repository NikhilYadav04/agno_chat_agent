from fastapi import APIRouter, HTTPException, Query
from backend.services import memory_service, file_service

router = APIRouter()

@router.post("/knowledge/clear", tags=["Maintenance"])
async def clear_knowledge(token: str = Query(..., description="User token to identify records")):
    """
    Wipes the Pinecone records for a specific user.
    """
    try:
        await file_service.clear_knowledge_base(token)
        return {"status": "success", "message": f"Knowledge base for user {token} cleared."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/memory/clear", tags=["Maintenance"])
async def clear_memory(token: str = Query(..., description="User token to identify records")):
    """
    Wipes the SQLite memory table for a specific user.
    """
    try:
        memory_service.clear_all_user_memories(token)
        return {"status": "success", "message": f"Memory for user {token} cleared."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
