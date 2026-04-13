from typing import Union, Optional
import tempfile
import zipfile
import shutil
import os
import aiofiles
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from src.infrastructure.models.validator_models import ValidationResponse, ValidationFailure, FileType
from src.infrastructure.services.unified_validator_service import UnifiedValidatorService
from src.infrastructure.services.temp_file_service import TempFileService
from src.api.models.api_models import ErrorResponse

router = APIRouter()

@router.post("/generate", response_model=Union[ErrorResponse], responses={200: {"content": {"application/zip": {}}}, 400: {"model": ErrorResponse}})
async def generate_api(
    file: UploadFile = File(...),
    file_type: FileType = Form(...),
    existing_project: Optional[UploadFile] = File(None)
):
    existing_project_dir = None
    try:
        # If user uploaded a previous project .zip, extract it to a temp dir
        if existing_project and existing_project.filename:
            existing_project_dir = tempfile.mkdtemp(prefix="existing_project_")
            zip_content = await existing_project.read()
            zip_path = os.path.join(existing_project_dir, "project.zip")
            async with aiofiles.open(zip_path, "wb") as zf:
                await zf.write(zip_content)
            with zipfile.ZipFile(zip_path, "r") as z:
                z.extractall(existing_project_dir)
            os.remove(zip_path)

        validation_result = await UnifiedValidatorService.validate_file(
            file, file_type.value, existing_project_dir=existing_project_dir
        )

        if isinstance(validation_result, str):
            return FileResponse(
                path=validation_result,
                media_type='application/zip',
                filename='generated_api.zip'
            )
        elif isinstance(validation_result, dict):
            return JSONResponse(
                status_code=400,
                content=validation_result
            )
        elif isinstance(validation_result, ValidationFailure):
            return JSONResponse(
                status_code=400,
                content=ErrorResponse(
                    message=validation_result.message,
                    errors=validation_result.errors
                ).model_dump(exclude_none=True)
            )
        else:
            return JSONResponse(
                status_code=500,
                content=ErrorResponse(message="Unexpected validation result").model_dump(exclude_none=True)
            )

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(message=f"Error processing file: {str(e)}").model_dump(exclude_none=True)
        )
    finally:
        # Clean up temp directory for existing project
        if existing_project_dir and os.path.isdir(existing_project_dir):
            shutil.rmtree(existing_project_dir, ignore_errors=True)
