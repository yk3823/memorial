"""
Photo API endpoints for Memorial Website.
Handles photo upload, management, and retrieval for memorial pages.
"""

import logging
from datetime import datetime
from typing import Annotated, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Request, File, UploadFile, Form
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.deps import (
    get_db,
    get_current_verified_user,
    get_client_ip
)
from app.core.config import get_settings
from app.services.photo import (
    PhotoService,
    get_photo_service,
    PhotoValidationError,
    PhotoProcessingError
)
from app.services.memorial import (
    MemorialService,
    get_memorial_service,
    MemorialNotFoundError,
    MemorialPermissionError
)
from app.schemas.photo import (
    PhotoType,
    PhotoUploadResponse,
    PhotoDeleteResponse,
    PhotoListResponse,
    PhotoResponse,
    PhotoReorderRequest,
    PhotoBatchUploadResponse
)
from app.models.user import User

logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(tags=["Photos"])

# Settings
settings = get_settings()

# Rate limiter
limiter = Limiter(key_func=get_remote_address)


@router.post(
    "/memorials/{memorial_id}/photos",
    response_model=PhotoUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload photo to memorial",
    description="Upload a photo for a memorial with specific photo type."
)
@limiter.limit("10/hour")  # Limit photo uploads
async def upload_photo(
    request: Request,
    memorial_id: Annotated[UUID, ...],
    photo_type: Annotated[PhotoType, Form(description="Type of photo")],
    file: Annotated[UploadFile, File(description="Photo file to upload")],
    caption: Annotated[str, Form(description="Optional photo caption")] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
    current_user: Annotated[User, Depends(get_current_verified_user)] = ...,
    photo_service: Annotated[PhotoService, Depends(get_photo_service)] = ...,
    memorial_service: Annotated[MemorialService, Depends(get_memorial_service)] = ...
) -> PhotoUploadResponse:
    """
    Upload a photo to a memorial.
    
    - **memorial_id**: UUID of the memorial to add photo to
    - **photo_type**: Type of photo (deceased, grave, memorial1-4)
    - **file**: Image file (JPG, PNG, WebP, GIF, max 10MB)
    - **caption**: Optional caption for the photo
    
    Returns upload status and photo information.
    """
    try:
        logger.info(f"Photo upload request for memorial {memorial_id} by user {current_user.id}")
        
        # Verify memorial exists and user has permission
        memorial = await memorial_service.get_memorial_by_id(
            db=db,
            memorial_id=memorial_id,
            user_id=current_user.id
        )
        
        if not memorial:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Memorial not found or access denied"
            )
        
        # Check if memorial is locked
        if memorial.is_locked:
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail="Memorial is locked and cannot be modified"
            )
        
        # Upload photo
        result = await photo_service.upload_photo(
            db=db,
            memorial_id=memorial_id,
            photo_type=photo_type,
            file=file,
            caption=caption,
            user_id=current_user.id
        )
        
        if result.success:
            logger.info(f"Photo uploaded successfully for memorial {memorial_id}")
            return result
        else:
            logger.warning(f"Photo upload failed: {result.message}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.message
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during photo upload: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Photo upload failed"
        )


@router.get(
    "/memorials/{memorial_id}/photos",
    response_model=PhotoListResponse,
    summary="List memorial photos",
    description="Get all photos for a memorial."
)
async def list_memorial_photos(
    memorial_id: Annotated[UUID, ...],
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
    current_user: Annotated[User, Depends(get_current_verified_user)] = ...,
    photo_service: Annotated[PhotoService, Depends(get_photo_service)] = ...,
    memorial_service: Annotated[MemorialService, Depends(get_memorial_service)] = ...
) -> PhotoListResponse:
    """
    List all photos for a memorial.
    
    Returns list of photos with metadata, ordered by display order.
    """
    try:
        logger.info(f"Listing photos for memorial {memorial_id}")
        
        # Verify memorial exists and user has permission
        memorial = await memorial_service.get_memorial_by_id(
            db=db,
            memorial_id=memorial_id,
            user_id=current_user.id
        )
        
        if not memorial:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Memorial not found or access denied"
            )
        
        # Get photos
        photos = await photo_service.get_photos_by_memorial(db, memorial_id)
        
        return PhotoListResponse(
            photos=photos,
            total=len(photos)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list photos for memorial {memorial_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve photos"
        )


@router.delete(
    "/photos/{photo_id}",
    response_model=PhotoDeleteResponse,
    summary="Delete photo",
    description="Delete a specific photo from a memorial."
)
@limiter.limit("20/hour")  # Limit photo deletions
async def delete_photo(
    request: Request,
    photo_id: Annotated[UUID, ...],
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
    current_user: Annotated[User, Depends(get_current_verified_user)] = ...,
    photo_service: Annotated[PhotoService, Depends(get_photo_service)] = ...
) -> PhotoDeleteResponse:
    """
    Delete a photo.
    
    Only the memorial owner or the photo uploader can delete photos.
    """
    try:
        logger.info(f"Delete photo request for {photo_id} by user {current_user.id}")
        
        # Delete photo
        result = await photo_service.delete_photo(
            db=db,
            photo_id=photo_id,
            user_id=current_user.id
        )
        
        if result.success:
            logger.info(f"Photo deleted successfully: {photo_id}")
            return result
        else:
            # Determine appropriate status code based on error message
            if "not found" in result.message.lower():
                status_code = status.HTTP_404_NOT_FOUND
            elif "permission denied" in result.message.lower():
                status_code = status.HTTP_403_FORBIDDEN
            else:
                status_code = status.HTTP_400_BAD_REQUEST
            
            raise HTTPException(
                status_code=status_code,
                detail=result.message
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during photo deletion: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Photo deletion failed"
        )


@router.post(
    "/memorials/{memorial_id}/photos/batch",
    response_model=PhotoBatchUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Batch upload photos",
    description="Upload multiple photos at once with different types."
)
@limiter.limit("3/hour")  # Stricter limit for batch uploads
async def batch_upload_photos(
    request: Request,
    memorial_id: Annotated[UUID, ...],
    files: Annotated[List[UploadFile], File(description="Photo files to upload")],
    photo_types: Annotated[List[PhotoType], Form(description="Photo types corresponding to files")],
    captions: Annotated[List[str], Form(description="Captions for each photo")] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
    current_user: Annotated[User, Depends(get_current_verified_user)] = ...,
    photo_service: Annotated[PhotoService, Depends(get_photo_service)] = ...,
    memorial_service: Annotated[MemorialService, Depends(get_memorial_service)] = ...
) -> PhotoBatchUploadResponse:
    """
    Upload multiple photos to a memorial at once.
    
    - **files**: List of image files
    - **photo_types**: List of photo types corresponding to each file
    - **captions**: Optional list of captions for each photo
    
    All lists must have the same length. Maximum 6 photos per batch.
    """
    try:
        logger.info(f"Batch photo upload for memorial {memorial_id} by user {current_user.id}")
        
        # Validate input lengths
        if len(files) != len(photo_types):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Number of files must match number of photo types"
            )
        
        if captions and len(captions) != len(files):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Number of captions must match number of files"
            )
        
        # Limit batch size
        if len(files) > 6:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Maximum 6 photos per batch upload"
            )
        
        # Verify memorial exists and user has permission
        memorial = await memorial_service.get_memorial_by_id(
            db=db,
            memorial_id=memorial_id,
            user_id=current_user.id
        )
        
        if not memorial:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Memorial not found or access denied"
            )
        
        if memorial.is_locked:
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail="Memorial is locked and cannot be modified"
            )
        
        # Process each upload
        uploaded_photos = []
        failed_uploads = []
        
        for i, (file, photo_type) in enumerate(zip(files, photo_types)):
            caption = captions[i] if captions and i < len(captions) else None
            
            try:
                result = await photo_service.upload_photo(
                    db=db,
                    memorial_id=memorial_id,
                    photo_type=photo_type,
                    file=file,
                    caption=caption,
                    user_id=current_user.id
                )
                
                if result.success and result.photo:
                    uploaded_photos.append(result.photo)
                else:
                    failed_uploads.append({
                        "filename": file.filename,
                        "photo_type": photo_type,
                        "error": result.message
                    })
                    
            except Exception as e:
                failed_uploads.append({
                    "filename": file.filename,
                    "photo_type": photo_type,
                    "error": str(e)
                })
        
        total_uploaded = len(uploaded_photos)
        total_failed = len(failed_uploads)
        
        # Determine response message
        if total_uploaded > 0 and total_failed == 0:
            message = f"All {total_uploaded} photos uploaded successfully"
            success = True
        elif total_uploaded > 0 and total_failed > 0:
            message = f"{total_uploaded} photos uploaded, {total_failed} failed"
            success = True  # Partial success
        else:
            message = f"All {total_failed} photo uploads failed"
            success = False
        
        logger.info(f"Batch upload completed: {total_uploaded} success, {total_failed} failed")
        
        return PhotoBatchUploadResponse(
            success=success,
            message=message,
            uploaded_photos=uploaded_photos,
            failed_uploads=failed_uploads,
            total_uploaded=total_uploaded,
            total_failed=total_failed
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during batch photo upload: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Batch photo upload failed"
        )


@router.put(
    "/photos/{photo_id}/reorder",
    response_model=PhotoResponse,
    summary="Reorder photo",
    description="Change the display order of a photo."
)
async def reorder_photo(
    photo_id: Annotated[UUID, ...],
    reorder_request: PhotoReorderRequest,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
    current_user: Annotated[User, Depends(get_current_verified_user)] = ...,
    photo_service: Annotated[PhotoService, Depends(get_photo_service)] = ...
) -> PhotoResponse:
    """
    Change the display order of a photo.
    
    This endpoint is for future implementation of custom photo ordering.
    Currently, photo order is determined by photo type.
    """
    # This is a placeholder for future implementation
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Photo reordering is not yet implemented. Order is determined by photo type."
    )


@router.get(
    "/photos/types",
    summary="Get photo types",
    description="Get list of valid photo types and their limits."
)
async def get_photo_types():
    """Get information about photo types and limits."""
    from app.models.photo import Photo
    
    return {
        "valid_types": Photo.get_valid_photo_types(),
        "type_limits": Photo.get_photo_type_limits(),
        "max_total_photos": Photo.get_max_photos_per_memorial(),
        "max_file_size_mb": Photo.get_max_file_size_mb(),
        "allowed_extensions": Photo.get_allowed_extensions()
    }