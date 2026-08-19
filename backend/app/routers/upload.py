"""
Upload endpoint for processing financial document files.
"""
import os
import uuid
import aiofiles
from typing import List
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, BackgroundTasks, Cookie, Response, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.config import get_settings
from app.models.financial_record import FinancialRecord
from app.models.schemas import UploadResponse, BulkUploadResponse
from app.utils.file_validation import validate_upload_file, generate_safe_filename, get_file_extension

router = APIRouter(prefix="/api", tags=["upload"])
settings = get_settings()


def get_session_id(session_id: str | None = Cookie(default=None), x_session_id: str | None = Header(default=None)) -> str:
    """Get or generate a session ID for user isolation."""
    sid = x_session_id or session_id
    if sid:
        return sid
    return str(uuid.uuid4())


@router.post("/upload", response_model=BulkUploadResponse)
async def upload_documents(
    background_tasks: BackgroundTasks,
    response: Response,
    files: List[UploadFile] = File(...),
    db: AsyncSession = Depends(get_db),
    session_id: str = Depends(get_session_id),
):
    """
    Upload one or more financial document files for processing.
    
    Accepts: PDF, PNG, JPG, JPEG, TIFF, WEBP
    Max size: 20MB per file
    
    The system will automatically classify each document (invoice, receipt,
    purchase order, or expense report) and extract structured data.
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")
    
    if len(files) > 20:
        raise HTTPException(status_code=400, detail="Maximum 20 files per upload")
    
    # Ensure upload directory exists
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    
    results = []
    successful = 0
    failed = 0
    
    for file in files:
        # Validate the file
        is_valid, error_message = await validate_upload_file(file)
        
        if not is_valid:
            results.append(UploadResponse(
                id=uuid.uuid4(),
                filename=file.filename or "unknown",
                status="failed",
                message=error_message,
            ))
            failed += 1
            continue
        
        # Create financial record
        record_id = uuid.uuid4()
        safe_filename = generate_safe_filename(file.filename or "unknown", str(record_id))
        file_path = os.path.join(settings.UPLOAD_DIR, safe_filename)
        
        # Read file content for size
        content = await file.read()
        await file.seek(0)
        
        # Save file to disk
        try:
            async with aiofiles.open(file_path, "wb") as f:
                await f.write(content)
        except Exception as e:
            results.append(UploadResponse(
                id=record_id,
                filename=file.filename or "unknown",
                status="failed",
                message=f"Failed to save file: {str(e)}",
            ))
            failed += 1
            continue
        
        # Create database record (record_type will be set during extraction)
        record = FinancialRecord(
            id=record_id,
            session_id=session_id,
            record_type="invoice",  # default, will be overwritten by AI classification
            original_filename=file.filename or "unknown",
            file_path=file_path,
            file_type=get_file_extension(file.filename or ""),
            file_size_bytes=len(content),
            status="processing",
        )
        db.add(record)
        
        # Queue background extraction
        from app.services.extraction.pipeline import process_record
        background_tasks.add_task(process_record, str(record_id))
        
        results.append(UploadResponse(
            id=record_id,
            filename=file.filename or "unknown",
            status="processing",
            message="File uploaded successfully. Classification and extraction in progress.",
        ))
        successful += 1
    
    # Commit all records
    await db.commit()
    
    # Ensure the session_id cookie is set
    response.set_cookie(
        key="session_id",
        value=session_id,
        max_age=60 * 60 * 24 * 30,  # 30 days
        httponly=True,
        samesite="lax",
    )
    
    return BulkUploadResponse(
        uploads=results,
        total=len(files),
        successful=successful,
        failed=failed,
    )
