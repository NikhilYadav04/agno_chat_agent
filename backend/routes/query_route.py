from typing import Optional
import uuid
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Header
from fastapi.responses import StreamingResponse

from backend.database import chat_repository
from backend.services import agent_service, file_service

router = APIRouter()


@router.post("/query")
async def query(
    authorization: Optional[str] = Header(None, description="Bearer JWT token"),
    token: str = Form(..., description="User ID"),
    user_message: str = Form(..., description="The user's query"),
    file: Optional[UploadFile] = File(None, description="Optional PDF or document"),
    latitude: str = Form("", description="Latitude of user's location"),
    longitude: str = Form("", description="Longitude of user's location"),
):
    """
    Main query endpoint.

    1. (Optional) Upload file → index into Pinecone.
    2. Fetch last 5 messages from Supabase as context.
    3. Stream agent response back to the client.
    4. After stream ends: persist user + agent messages, apply FIFO pruning.
    """
    if not token or not token.strip():
        raise HTTPException(status_code=400, detail="token is required.")
    if not user_message or not user_message.strip():
        raise HTTPException(status_code=400, detail="user_message is required.")

    # ── Step 1: File upload (if provided) ──
    if file and file.filename:
        try:
            file_bytes = await file.read()
            await file_service.upload_file_to_knowledge(
                file_bytes, file.filename, token
            )
        except ValueError as e:
            raise HTTPException(status_code=422, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"File upload failed: {e}")

    # ── Step 2: Fetch recent history for context ──
    try:
        recent_history = chat_repository.fetch_recent(token, limit=10)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch history: {e}")

    # ── Step 3 + 4: Stream and persist ──
    user_msg_id = str(uuid.uuid4())
    agent_msg_id = str(uuid.uuid4())

    print(f"The user query is ${user_message}")

    jwt_token = ""
    if authorization and authorization.startswith("Bearer "):
        jwt_token = authorization.split("Bearer ")[1]

    async def response_generator():
        full_response = ""
        try:
            async for chunk in agent_service.stream_agent_response(
                token,
                user_message,
                recent_history,
                agent_msg_id,
                jwt_token,
                latitude=latitude,
                longitude=longitude,
            ):
                full_response += chunk
                yield chunk
        except Exception as e:
            yield f"\n[Agent Error]: {e}"
            return

        # Persist after stream completes
        try:
            chat_repository.insert_message(
                token, "user", user_message, message_id=user_msg_id
            )
            chat_repository.insert_message(
                token, "agent", full_response, message_id=agent_msg_id
            )
        except Exception as e:
            yield f"\n[Storage Error]: {e}"

    return StreamingResponse(response_generator(), media_type="text/plain")
