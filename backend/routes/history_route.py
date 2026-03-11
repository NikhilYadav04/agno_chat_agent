from fastapi import APIRouter, HTTPException, Query
from backend.database import chat_repository

router = APIRouter()


@router.get("/history")
async def get_history(
    token: str = Query(..., description="User token"),
    page: int = Query(1, description="Page number for pagination", ge=1),
    limit: int = Query(20, description="Number of items per page", ge=1, le=100)
):
    """
    Returns the paginated conversation history for a token in chronological order.
    """
    if not token or not token.strip():
        raise HTTPException(status_code=400, detail="token is required.")
    try:
        result = chat_repository.fetch_all(token, page, limit)
        totalPages = (result["total"] + limit - 1) // limit if result["total"] > 0 else 0
        return {
            "token": token, 
            "history": result["data"],
            "pagination": {
                "page": page,
                "limit": limit,
                "total": result["total"],
                "totalPages": totalPages,
                "hasMore": page < totalPages
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch history: {e}")


@router.delete("/history")
async def clear_history(token: str = Query(..., description="User token")):
    """
    Deletes all conversation history for a token.
    """
    if not token or not token.strip():
        raise HTTPException(status_code=400, detail="token is required.")
    try:
        chat_repository.delete_all(token)
        return {"status": "success", "message": f"History cleared for token."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear history: {e}")
