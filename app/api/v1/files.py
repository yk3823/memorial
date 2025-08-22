"""
File serving API endpoints for Memorial Website.
Serves photos and videos with proper access control.
"""

import logging
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, status, Depends, Path as PathParam
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db, get_current_user
from app.core.config import get_settings
from app.models.user import User
from app.models.memorial import Memorial
from app.models.photo import Photo
from app.services.file_storage import get_file_storage_service

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Files"])
settings = get_settings()

@router.get(
    "/photos/{memorial_id}/{filename}",
    summary="Serve memorial photo",
    description="Serve a photo file for a memorial (public if memorial is public)"
)
async def serve_photo(
    memorial_id: str = PathParam(..., description="Memorial ID"),
    filename: str = PathParam(..., description="Photo filename"),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    """
    Serve a photo file.
    
    Access control:
    - Public memorials: Anyone can access
    - Private memorials: Only the owner can access
    """
    try:
        # Get memorial to check access permissions
        from sqlalchemy import select
        result = await db.execute(
            select(Memorial).where(Memorial.id == memorial_id)
        )
        memorial = result.scalar_one_or_none()
        
        if not memorial:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Memorial not found"
            )
        
        # Check access permissions
        if not memorial.is_public:
            if not current_user or memorial.owner_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied"
                )
        
        # Construct file path
        file_path = Path(settings.PHOTOS_FOLDER) / memorial_id / filename
        
        if not file_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Photo not found"
            )
        
        # Determine media type
        media_type = "image/jpeg"
        if filename.lower().endswith(('.png')):
            media_type = "image/png"
        elif filename.lower().endswith(('.gif')):
            media_type = "image/gif"
        elif filename.lower().endswith(('.webp')):
            media_type = "image/webp"
        
        return FileResponse(
            path=str(file_path),
            media_type=media_type,
            filename=filename
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to serve photo {memorial_id}/{filename}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to serve photo"
        )


@router.get(
    "/videos/{memorial_id}/{filename}",
    summary="Serve memorial video",
    description="Serve a video file for a memorial (public if memorial is public)"
)
async def serve_video(
    memorial_id: str = PathParam(..., description="Memorial ID"),
    filename: str = PathParam(..., description="Video filename"),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    """
    Serve a video file.
    
    Access control:
    - Public memorials: Anyone can access
    - Private memorials: Only the owner can access
    """
    try:
        # Get memorial to check access permissions
        from sqlalchemy import select
        result = await db.execute(
            select(Memorial).where(Memorial.id == memorial_id)
        )
        memorial = result.scalar_one_or_none()
        
        if not memorial:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Memorial not found"
            )
        
        # Check access permissions
        if not memorial.is_public:
            if not current_user or memorial.owner_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied"
                )
        
        # Construct file path
        file_path = Path(settings.VIDEOS_FOLDER) / memorial_id / filename
        
        if not file_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Video not found"
            )
        
        # Determine media type
        media_type = "video/mp4"
        if filename.lower().endswith(('.avi')):
            media_type = "video/x-msvideo"
        elif filename.lower().endswith(('.mov')):
            media_type = "video/quicktime"
        elif filename.lower().endswith(('.wmv')):
            media_type = "video/x-ms-wmv"
        
        return FileResponse(
            path=str(file_path),
            media_type=media_type,
            filename=filename
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to serve video {memorial_id}/{filename}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to serve video"
        )


@router.get(
    "/thumbnails/{memorial_id}/{filename}",
    summary="Serve photo thumbnail",
    description="Serve a thumbnail for a photo"
)
async def serve_thumbnail(
    memorial_id: str = PathParam(..., description="Memorial ID"),
    filename: str = PathParam(..., description="Thumbnail filename"),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    """
    Serve a photo thumbnail.
    
    Access control same as photos.
    """
    try:
        # Get memorial to check access permissions
        from sqlalchemy import select
        result = await db.execute(
            select(Memorial).where(Memorial.id == memorial_id)
        )
        memorial = result.scalar_one_or_none()
        
        if not memorial:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Memorial not found"
            )
        
        # Check access permissions
        if not memorial.is_public:
            if not current_user or memorial.owner_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied"
                )
        
        # Construct thumbnail file path (with thumb_ prefix)
        thumbnail_filename = f"thumb_{filename}"
        file_path = Path(settings.PHOTOS_FOLDER) / memorial_id / thumbnail_filename
        
        if not file_path.exists():
            # If thumbnail doesn't exist, serve the original image
            original_path = Path(settings.PHOTOS_FOLDER) / memorial_id / filename
            if original_path.exists():
                file_path = original_path
            else:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Thumbnail not found"
                )
        
        return FileResponse(
            path=str(file_path),
            media_type="image/jpeg",
            filename=thumbnail_filename
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to serve thumbnail {memorial_id}/{filename}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to serve thumbnail"
        )