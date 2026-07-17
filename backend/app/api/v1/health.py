from fastapi import APIRouter
from app.schemas.response import StandardResponse

router = APIRouter()


@router.get("/health", tags=["Health"], response_model=StandardResponse[dict])
async def health_check():
    """
    Health check endpoint.
    Used by Kubernetes, Azure Monitor,
    Load balancers and monitoring tools.
    """
    return StandardResponse(
        data={
            "status": "healthy",
            "service": "Enterprise IT Operations Automation Platform",
            "version": "0.1.0"
        }
    )


