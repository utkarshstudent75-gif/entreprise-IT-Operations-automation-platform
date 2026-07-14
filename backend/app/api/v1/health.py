from fastapi import APIRouter

router = APIRouter()


@router.get("/health", tags=["Health"])
async def health_check():

    """

    Health check endpoint.
    Used by Kubernetes, Azure Monitor,
    Load balancers and monitoring tools.
    """

    return {
            "status": "healthy",
            "service": "Enterprise IT Operations Automation Platform",
            "version": "0.1.0"
        
            }

