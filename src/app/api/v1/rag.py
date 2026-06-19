from fastapi import APIRouter, status

router = APIRouter(prefix="/rag", tags=["rag"])


# ----------------- Test Endpoint -----------------
@router.get("/rag-test", status_code=status.HTTP_200_OK)
async def get_rag() -> dict[str, str]:
    return {"message": "RAG API is working"}


# ----------------- Ingest Data Endpoint -----------------
@router.post("/ingest-data", status_code=status.HTTP_204_NO_CONTENT)
async def ingest_data() -> None:
    return None


# ----------------- Query Data Endpoint -----------------
@router.post("/query-data", status_code=status.HTTP_204_NO_CONTENT)
async def query_data() -> None:
    return None