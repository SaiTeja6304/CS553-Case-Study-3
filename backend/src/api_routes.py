from fastapi import APIRouter, HTTPException, File, UploadFile, Form, Response
from .services import generate_response_api, generate_response_local
from time import perf_counter
import prometheus_client

router = APIRouter( 
   prefix="/api",  
   tags=["VLM Chat API"]  
) 

API_BACKEND_REQUESTS_TOTAL = prometheus_client.Counter(
    'api_backend_requests_total',
    'Total number of API requests made.'
)

LOCAL_BACKEND_REQUESTS_TOTAL = prometheus_client.Counter(
    'local_backend_requests_total',
    'Total number of local requests made.'
)

API_BACKEND_ERRORS_TOTAL = prometheus_client.Counter(
    'api_backend_errors_total',
    'Total number of API request errors occured in backend.'
)

LOCAL_BACKEND_ERRORS_TOTAL = prometheus_client.Counter(
    'local_backend_errors_total',
    'Total number of local request errors occured in backend.'
)

API_BACKEND_REQUESTTIME_SECONDS = prometheus_client.Histogram(
    'api_backend_requesttime_seconds',
    'Total time spent processing backend API requests.'
)

LOCAL_BACKEND_REQUESTTIME_SECONDS = prometheus_client.Histogram(
    'local_backend_requesttime_seconds',
    'Total time spent processing backend local requests.'
)

HEALTH_CHECK_REQUESTS_TOTAL = prometheus_client.Counter(
    'health_check_requests_total',
    'Total number of health check requests.'
)

@router.get("/", status_code=200, response_model=dict)
async def root():
    HEALTH_CHECK_REQUESTS_TOTAL.inc()
    """Root endpoint for the VLM Chat API"""
    return {"message": "VLM Chat API", "status": "running"}

@router.get('/metrics', status_code=200)
async def metrics():
    return Response(
        content = prometheus_client.generate_latest(),
        media_type= prometheus_client.CONTENT_TYPE_LATEST
    )

@router.post("/generate-response-local", status_code=200, response_model=dict)
async def generate_response_local_route(input_img: UploadFile = File(...), query: str = Form(...), chat_history: str = Form("")):
    """Generate response using local model"""
    LOCAL_BACKEND_REQUESTS_TOTAL.inc()
    local_start_time = perf_counter()
    try:
        result = await generate_response_local(input_img, query, True, chat_history)
        if result["db_insert"] != "Successfully inserted log":
            raise HTTPException(status_code=500, detail=result["db_insert"])
        return result
    except HTTPException:
        LOCAL_BACKEND_ERRORS_TOTAL.inc()
        raise
    except Exception as e:
        LOCAL_BACKEND_ERRORS_TOTAL.inc()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        LOCAL_BACKEND_REQUESTTIME_SECONDS.observe(perf_counter() - local_start_time)


@router.post("/generate-response-api", status_code=200, response_model=dict)
async def generate_response_api_route(input_img: UploadFile = File(...), query: str = Form(...), chat_history: str = Form("")):
    """Generate response using HF Inference API"""
    API_BACKEND_REQUESTS_TOTAL.inc()
    api_start_time = perf_counter()
    try:
        result = await generate_response_api(input_img, query, False, chat_history)
        if result["db_insert"] != "Successfully inserted log":
            raise HTTPException(status_code=500, detail=result["db_insert"])
        return result
    except HTTPException:
        API_BACKEND_ERRORS_TOTAL.inc()
        raise
    except Exception as e:
        API_BACKEND_ERRORS_TOTAL.inc()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        API_BACKEND_REQUESTTIME_SECONDS.observe(perf_counter() - api_start_time)

