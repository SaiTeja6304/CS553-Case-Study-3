from fastapi import FastAPI 
from .api_routes import router
from .db import close_connection
from .services import conn, cursor 
 
# Create FastAPI app
app = FastAPI( 
   title="VLM Chat", 
   version="1.0.0" 
) 
 
 
# Include the routers 
app.include_router(router) 
 
@app.on_event("shutdown")
def shutdown():
    close_connection(conn, cursor)

# uvicorn backend.src.app:app --host 0.0.0.0 --port 9011 --reload