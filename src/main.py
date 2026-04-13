import os

import uvicorn
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.staticfiles import StaticFiles

from src.api.handlers.custom_exception import CustomException
from src.api.handlers.exception_handlers import validation_exception_handler, custom_exception_handler
from src.config import custom_openapi, config_logs

# init
config_logs()
app = FastAPI()

# static
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app.mount("/definition", StaticFiles(directory=os.path.join(BASE_DIR, "definition")), name="definition")

# openapi
app.get("/openapi.json", include_in_schema=False)(custom_openapi)
app.openapi = custom_openapi

# routers
from src.api.routes.generate_router import router as GenerateRouter

# routers
app.include_router(GenerateRouter, prefix="/api")

# handlers

# handlers
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(CustomException, custom_exception_handler)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
