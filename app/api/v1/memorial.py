"""
Memorial API endpoints for Memorial Website.
Handles memorial CRUD operations, search, and Hebrew calendar integration.
"""

import logging
from datetime import datetime
from typing import Annotated, Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Request, Query, Path, Form, File, UploadFile
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.deps import (
    get_db,
    get_current_user,
    get_current_active_user,
    get_current_verified_user,
    get_pagination,
    PaginationParams,
    get_client_ip
)
from app.core.config import get_settings
from app.services.memorial import (
    MemorialService,
    get_memorial_service,
    MemorialError,
    MemorialNotFoundError,
    MemorialPermissionError,
    MemorialValidationError
)
from app.services.file_storage import get_file_storage_service
from app.schemas.memorial_simple import (
    MemorialCreate,
    MemorialUpdate,
    MemorialResponse,
    PublicMemorialResponse,
    MemorialListResponse,
    MemorialSearchRequest,
    MemorialSearchResponse,
    MemorialStatsResponse,
    MemorialSlugRequest,
    MemorialSlugResponse,
    MemorialWithPhotos,
    MemorialVisibilityRequest,
    MemorialLockRequest,
    MemorialCreateResponse,
    MemorialUpdateResponse,
    MemorialDeleteResponse,
    MemorialError as MemorialErrorSchema
)
from app.models.user import User
from app.models.memorial import Memorial
from app.models.photo import Photo
from app.schemas.photo import PhotoResponse
from sqlalchemy import select

logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(tags=["Memorials"])

# Settings
settings = get_settings()

# Rate limiter
limiter = Limiter(key_func=get_remote_address)


# Memorial CRUD Operations

@router.post(
    "",
    response_model=MemorialCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create new memorial",
    description="Create a new memorial page with Hebrew calendar integration."
)
@limiter.limit("10/hour")  # Limit memorial creation
async def create_memorial(
    request: Request,
    memorial_data: MemorialCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_verified_user)],
    memorial_service: Annotated[MemorialService, Depends(get_memorial_service)]
) -> MemorialCreateResponse:
    """
    Create a new memorial.
    
    - **deceased_name_hebrew**: Name of the deceased in Hebrew (required)
    - **deceased_name_english**: Name of the deceased in English (optional)
    - **birth_date_gregorian**: Birth date in Gregorian calendar
    - **birth_date_hebrew**: Birth date in Hebrew calendar
    - **death_date_gregorian**: Death date in Gregorian calendar
    - **death_date_hebrew**: Death date in Hebrew calendar
    - **biography**: Biography and life story
    - **memorial_song_url**: URL to memorial song or audio file
    - **is_public**: Whether the memorial is publicly viewable
    
    Returns created memorial with computed fields and public URL if applicable.
    """
    try:
        logger.info(f"Creating memorial for user {current_user.id}")
        
        # Check if user can create memorial (subscription + limits)
        # Get memorial count using async query to avoid greenlet issues
        from sqlalchemy import select, func
        result = await db.execute(
            select(func.count(Memorial.id)).where(
                Memorial.owner_id == current_user.id,
                Memorial.is_deleted == False
            )
        )
        active_memorials_count = result.scalar() or 0
        
        # Check basic subscription requirements
        if not (current_user.is_active and current_user.is_verified and current_user.is_subscription_active()):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="חשבון לא מאומת. אנא אמת את כתובת האימייל שלך דרך הקישור שנשלח אליך"
            )
        
        # Check memorial limit
        if active_memorials_count >= current_user.max_memorials:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"הגעת למגבלה של {current_user.max_memorials} אזכרות. לייצור אזכרות נוספות, שדרג את החשבון שלך."
            )
        
        # Create memorial
        memorial = await memorial_service.create_memorial(
            db=db,
            memorial_data=memorial_data,
            owner_id=current_user.id
        )
        
        # Convert to response schema with explicit field mapping to avoid async issues
        memorial_response = MemorialResponse(
            id=memorial.id,
            owner_id=memorial.owner_id,
            deceased_name_hebrew=memorial.deceased_name_hebrew,
            deceased_name_english=memorial.deceased_name_english,
            birth_date_gregorian=memorial.birth_date_gregorian,
            birth_date_hebrew=memorial.birth_date_hebrew,
            death_date_gregorian=memorial.death_date_gregorian,
            death_date_hebrew=memorial.death_date_hebrew,
            yahrzeit_date_hebrew=memorial.yahrzeit_date_hebrew,
            next_yahrzeit_gregorian=memorial.next_yahrzeit_gregorian,
            biography=memorial.biography,
            memorial_song_url=memorial.memorial_song_url,
            is_locked=memorial.is_locked,
            is_public=memorial.is_public,
            page_views=memorial.page_views,
            unique_slug=memorial.unique_slug,
            created_at=memorial.created_at,
            updated_at=memorial.updated_at,
            display_name=memorial.display_name,
            age_at_death=memorial.age_at_death,
            public_url=memorial.public_url,
            years_since_death=memorial.years_since_death
        )
        
        # Generate public URL if applicable
        public_url = None
        if memorial.is_public and memorial.unique_slug:
            public_url = f"/memorial/{memorial.unique_slug}"
        
        logger.info(f"Memorial created successfully: {memorial.id}")
        
        return MemorialCreateResponse(
            success=True,
            message="Memorial created successfully",
            memorial=memorial_response,
            public_url=public_url
        )
        
    except MemorialValidationError as e:
        logger.warning(f"Memorial creation validation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except MemorialError as e:
        logger.error(f"Memorial creation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create memorial"
        )
    except Exception as e:
        logger.error(f"Unexpected error during memorial creation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post(
    "/with-files",
    response_model=MemorialCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create new memorial with file uploads",
    description="Create a new memorial page with photos, video, and Hebrew calendar integration."
)
@limiter.limit("10/hour")  # Limit memorial creation
async def create_memorial_with_files(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_verified_user)],
    memorial_service: Annotated[MemorialService, Depends(get_memorial_service)],
    
    # Required fields
    hebrew_first_name: Annotated[str, Form(...)],
    hebrew_last_name: Annotated[str, Form(...)],
    parent_name_hebrew: Annotated[str, Form(...)],
    
    # Optional text fields (deceased_name_hebrew can be computed if not provided)
    deceased_name_hebrew: Annotated[Optional[str], Form()] = None,
    english_first_name: Annotated[Optional[str], Form()] = None,
    english_last_name: Annotated[Optional[str], Form()] = None,
    deceased_name_english: Annotated[Optional[str], Form()] = None,
    
    # Family relationship fields (all optional)
    spouse_name: Annotated[Optional[str], Form()] = None,
    children_names: Annotated[Optional[str], Form()] = None,
    parents_names: Annotated[Optional[str], Form()] = None,
    family_names: Annotated[Optional[str], Form()] = None,
    birth_date_gregorian: Annotated[Optional[str], Form()] = None,
    birth_date_hebrew: Annotated[Optional[str], Form()] = None,
    death_date_gregorian: Annotated[Optional[str], Form()] = None,
    death_date_hebrew: Annotated[Optional[str], Form()] = None,
    biography: Annotated[Optional[str], Form()] = None,
    memorial_song_url: Annotated[Optional[str], Form()] = None,
    unique_slug: Annotated[Optional[str], Form()] = None,
    location: Annotated[Optional[str], Form()] = None,
    location_lat: Annotated[Optional[str], Form()] = None,
    location_lng: Annotated[Optional[str], Form()] = None,
    is_public: Annotated[Optional[str], Form()] = None,
    enable_comments: Annotated[Optional[str], Form()] = None,
    whatsapp_phones: Annotated[Optional[str], Form()] = None,
    notification_emails: Annotated[Optional[str], Form()] = None,
    
    # File uploads
    photo_0: Annotated[Optional[UploadFile], File()] = None,
    photo_1: Annotated[Optional[UploadFile], File()] = None,
    photo_2: Annotated[Optional[UploadFile], File()] = None,
    photo_3: Annotated[Optional[UploadFile], File()] = None,
    video: Annotated[Optional[UploadFile], File()] = None
) -> MemorialCreateResponse:
    """
    Create a new memorial with file uploads.
    
    This endpoint handles FormData submissions with files and creates
    a memorial with photos and video uploads.
    """
    try:
        logger.info(f"Creating memorial with files for user {current_user.id}")
        
        # Check if user can create memorial (subscription + limits)
        # Get memorial count using async query to avoid greenlet issues
        from sqlalchemy import select, func
        result = await db.execute(
            select(func.count(Memorial.id)).where(
                Memorial.owner_id == current_user.id,
                Memorial.is_deleted == False
            )
        )
        active_memorials_count = result.scalar() or 0
        
        # Check basic subscription requirements
        if not (current_user.is_active and current_user.is_verified and current_user.is_subscription_active()):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="חשבון לא מאומת. אנא אמת את כתובת האימייל שלך דרך הקישור שנשלח אליך"
            )
        
        # Check memorial limit
        if active_memorials_count >= current_user.max_memorials:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"הגעת למגבלה של {current_user.max_memorials} אזכרות. לייצור אזכרות נוספות, שדרג את החשבון שלך."
            )
        
        # Parse form data into MemorialCreate schema
        import json
        
        # Compute deceased_name_hebrew if not provided
        if not deceased_name_hebrew:
            deceased_name_hebrew = f"{hebrew_first_name} {hebrew_last_name}".strip()
        
        # Parse dates
        birth_date_parsed = None
        if birth_date_gregorian:
            try:
                from datetime import datetime
                birth_date_parsed = datetime.strptime(birth_date_gregorian, '%Y-%m-%d').date()
            except ValueError:
                pass
        
        death_date_parsed = None
        if death_date_gregorian:
            try:
                from datetime import datetime
                death_date_parsed = datetime.strptime(death_date_gregorian, '%Y-%m-%d').date()
            except ValueError:
                pass
        
        # Parse coordinates
        lat_parsed = None
        if location_lat:
            try:
                lat_parsed = float(location_lat)
            except ValueError:
                pass
                
        lng_parsed = None
        if location_lng:
            try:
                lng_parsed = float(location_lng)
            except ValueError:
                pass
        
        # Parse contact lists
        whatsapp_phones_parsed = None
        if whatsapp_phones:
            try:
                whatsapp_phones_parsed = json.loads(whatsapp_phones)
            except json.JSONDecodeError:
                pass
        
        notification_emails_parsed = None
        if notification_emails:
            try:
                notification_emails_parsed = json.loads(notification_emails)
            except json.JSONDecodeError:
                pass
        
        # Create memorial data object
        memorial_data = MemorialCreate(
            hebrew_first_name=hebrew_first_name,
            hebrew_last_name=hebrew_last_name,
            parent_name_hebrew=parent_name_hebrew,
            deceased_name_hebrew=deceased_name_hebrew,
            english_first_name=english_first_name,
            english_last_name=english_last_name,
            deceased_name_english=deceased_name_english,
            spouse_name=spouse_name,
            children_names=children_names,
            parents_names=parents_names,
            family_names=family_names,
            birth_date_gregorian=birth_date_parsed,
            birth_date_hebrew=birth_date_hebrew,
            death_date_gregorian=death_date_parsed,
            death_date_hebrew=death_date_hebrew,
            biography=biography,
            memorial_song_url=memorial_song_url,
            unique_slug=unique_slug,
            is_public=is_public == 'true' if is_public else True,
            enable_comments=enable_comments == 'true' if enable_comments else False,
            location=location,
            location_lat=lat_parsed,
            location_lng=lng_parsed,
            whatsapp_phones=whatsapp_phones_parsed,
            notification_emails=notification_emails_parsed
        )
        
        # Create memorial
        memorial = await memorial_service.create_memorial(
            db=db,
            memorial_data=memorial_data,
            owner_id=current_user.id
        )
        
        # Handle file uploads (photos and video)
        photos = [photo_0, photo_1, photo_2, photo_3]
        uploaded_photos = []
        uploaded_video = None
        
        file_storage = get_file_storage_service()
        memorial_id_str = str(memorial.id)
        
        # Save photos
        for i, photo in enumerate(photos):
            if photo and photo.filename:
                try:
                    photo_info = await file_storage.save_photo(photo, memorial_id_str)
                    uploaded_photos.append({
                        'index': i,
                        'photo_id': photo_info['photo_id'],
                        'filename': photo_info['filename'],
                        'original_filename': photo_info['original_filename'],
                        'size': photo_info['size'],
                        'url': f"/api/v1/files/photos/{memorial_id_str}/{photo_info['filename']}",
                        'thumbnail_url': f"/api/v1/files/thumbnails/{memorial_id_str}/{photo_info['filename']}"
                    })
                    logger.info(f"Photo {i} saved successfully: {photo_info['filename']}")
                except Exception as e:
                    logger.error(f"Failed to save photo {i}: {e}")
        
        # Save video
        if video and video.filename:
            try:
                video_info = await file_storage.save_video(video, memorial_id_str)
                uploaded_video = {
                    'video_id': video_info['video_id'],
                    'filename': video_info['filename'],
                    'original_filename': video_info['original_filename'],
                    'size': video_info['size'],
                    'duration_seconds': video_info['duration_seconds'],
                    'url': f"/api/v1/files/videos/{memorial_id_str}/{video_info['filename']}"
                }
                logger.info(f"Video saved successfully: {video_info['filename']}")
            except Exception as e:
                logger.error(f"Failed to save video: {e}")
                uploaded_video = None
        
        # Convert to response schema with explicit field mapping
        memorial_response = MemorialResponse(
            id=memorial.id,
            owner_id=memorial.owner_id,
            deceased_name_hebrew=memorial.deceased_name_hebrew,
            deceased_name_english=memorial.deceased_name_english,
            parent_name_hebrew=memorial.parent_name_hebrew,
            spouse_name=memorial.spouse_name,
            children_names=memorial.children_names,
            parents_names=memorial.parents_names,
            family_names=memorial.family_names,
            birth_date_gregorian=memorial.birth_date_gregorian,
            birth_date_hebrew=memorial.birth_date_hebrew,
            death_date_gregorian=memorial.death_date_gregorian,
            death_date_hebrew=memorial.death_date_hebrew,
            yahrzeit_date_hebrew=memorial.yahrzeit_date_hebrew,
            next_yahrzeit_gregorian=memorial.next_yahrzeit_gregorian,
            biography=memorial.biography,
            memorial_song_url=memorial.memorial_song_url,
            is_locked=memorial.is_locked,
            is_public=memorial.is_public,
            page_views=memorial.page_views,
            unique_slug=memorial.unique_slug,
            created_at=memorial.created_at,
            updated_at=memorial.updated_at,
            display_name=memorial.display_name,
            age_at_death=memorial.age_at_death,
            public_url=memorial.public_url,
            years_since_death=memorial.years_since_death
        )
        
        # Generate public URL if applicable
        public_url = None
        if memorial.is_public and memorial.unique_slug:
            public_url = f"/memorial/{memorial.unique_slug}"
        
        logger.info(f"Memorial with files created successfully: {memorial.id}")
        
        response_data = {
            "success": True,
            "message": "Memorial created successfully with files",
            "memorial": memorial_response,
            "public_url": public_url,
            "uploaded_files": {
                "photos": uploaded_photos,
                "video": uploaded_video,
                "total_photos": len(uploaded_photos),
                "has_video": uploaded_video is not None
            }
        }
        
        return response_data
        
    except MemorialValidationError as e:
        logger.warning(f"Memorial creation validation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except MemorialError as e:
        logger.error(f"Memorial creation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create memorial: {str(e)}"
        )
    except Exception as e:
        import traceback
        logger.error(f"Unexpected error during memorial creation: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.get(
    "/my",
    response_model=MemorialListResponse,
    summary="List current user's memorials", 
    description="Get paginated list of memorials owned by the current user."
)
async def list_my_memorials(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    pagination: Annotated[PaginationParams, Depends(get_pagination)],
    memorial_service: Annotated[MemorialService, Depends(get_memorial_service)],
    include_photos: bool = Query(False, description="Include photos in response")
) -> MemorialListResponse:
    """
    Get paginated list of memorials owned by current user.
    
    This endpoint specifically returns memorials owned by the authenticated user.
    
    Query parameters:
    - **skip**: Number of items to skip (default: 0)
    - **limit**: Maximum number of items to return (default: 20, max: 100)
    - **include_photos**: Include photos in response (default: false)
    """
    try:
        logger.info(f"Listing memorials for user {current_user.id} ({current_user.email})")
        
        result = await memorial_service.get_user_memorials(
            db=db,
            user_id=current_user.id,
            skip=pagination.skip,
            limit=pagination.limit,
            include_photos=include_photos
        )
        
        logger.info(f"Retrieved {len(result.items)} memorials for user {current_user.id}")
        return result
        
    except Exception as e:
        logger.error(f"Failed to list memorials for user {current_user.id}: {e}")
        logger.exception("Full error details:")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve memorials"
        )


@router.get(
    "",
    response_model=MemorialListResponse,
    summary="List user's memorials",
    description="Get paginated list of memorials owned by the current user."
)
async def list_user_memorials(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    pagination: Annotated[PaginationParams, Depends(get_pagination)],
    memorial_service: Annotated[MemorialService, Depends(get_memorial_service)],
    include_photos: bool = Query(False, description="Include photos in response")
) -> MemorialListResponse:
    """
    Get paginated list of memorials owned by current user.
    
    Query parameters:
    - **skip**: Number of items to skip (default: 0)
    - **limit**: Maximum number of items to return (default: 20, max: 100)
    - **include_photos**: Include photos in response (default: false)
    """
    try:
        logger.info(f"Listing memorials for user {current_user.id}")
        
        result = await memorial_service.get_user_memorials(
            db=db,
            user_id=current_user.id,
            skip=pagination.skip,
            limit=pagination.limit,
            include_photos=include_photos
        )
        
        logger.info(f"Retrieved {len(result.items)} memorials for user {current_user.id}")
        return result
        
    except Exception as e:
        logger.error(f"Failed to list memorials for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve memorials"
        )


@router.get(
    "/{memorial_id}",
    response_model=MemorialWithPhotos,
    summary="Get memorial details",
    description="Get detailed memorial information with photos."
)
async def get_memorial(
    memorial_id: Annotated[UUID, Path(..., description="Memorial ID")],
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    memorial_service: Annotated[MemorialService, Depends(get_memorial_service)]
) -> MemorialWithPhotos:
    """
    Get detailed memorial information.
    
    Returns memorial data with embedded photos and computed fields.
    User must be the owner or memorial must be public.
    """
    try:
        logger.info(f"Getting memorial {memorial_id} for user {current_user.id}")
        
        memorial = await memorial_service.get_memorial_by_id(
            db=db,
            memorial_id=memorial_id,
            user_id=current_user.id,
            include_photos=True
        )
        
        if not memorial:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Memorial not found or access denied"
            )
        
        # Convert to response schema with photos
        # Add photos
        photos = []
        primary_photo = None
        for photo in memorial.photos:
            if not photo.is_deleted:
                photo_dict = photo.to_dict()
                photos.append(photo_dict)
                if photo.is_primary:
                    primary_photo = photo_dict
        
        memorial_response = MemorialWithPhotos(
            id=memorial.id,
            owner_id=memorial.owner_id,
            deceased_name_hebrew=memorial.deceased_name_hebrew,
            deceased_name_english=memorial.deceased_name_english,
            birth_date_gregorian=memorial.birth_date_gregorian,
            birth_date_hebrew=memorial.birth_date_hebrew,
            death_date_gregorian=memorial.death_date_gregorian,
            death_date_hebrew=memorial.death_date_hebrew,
            yahrzeit_date_hebrew=memorial.yahrzeit_date_hebrew,
            next_yahrzeit_gregorian=memorial.next_yahrzeit_gregorian,
            biography=memorial.biography,
            memorial_song_url=memorial.memorial_song_url,
            is_locked=memorial.is_locked,
            is_public=memorial.is_public,
            page_views=memorial.page_views,
            unique_slug=memorial.unique_slug,
            created_at=memorial.created_at,
            updated_at=memorial.updated_at,
            display_name=memorial.display_name,
            age_at_death=memorial.age_at_death,
            public_url=memorial.public_url,
            years_since_death=memorial.years_since_death,
            photos=photos,
            primary_photo=primary_photo
        )
        
        logger.info(f"Memorial {memorial_id} retrieved successfully")
        return memorial_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get memorial {memorial_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve memorial"
        )


@router.put(
    "/{memorial_id}",
    response_model=MemorialUpdateResponse,
    summary="Update memorial",
    description="Update memorial information with partial updates supported."
)
@limiter.limit("30/hour")  # Limit memorial updates
async def update_memorial(
    request: Request,
    memorial_id: Annotated[UUID, Path(..., description="Memorial ID")],
    memorial_update: MemorialUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_verified_user)],
    memorial_service: Annotated[MemorialService, Depends(get_memorial_service)]
) -> MemorialUpdateResponse:
    """
    Update memorial information.
    
    All fields are optional for partial updates.
    User must be the memorial owner and memorial must not be locked.
    """
    try:
        logger.info(f"Updating memorial {memorial_id} for user {current_user.id}")
        
        # Track which fields were provided for update
        update_data = memorial_update.dict(exclude_unset=True)
        changes = list(update_data.keys())
        
        memorial = await memorial_service.update_memorial(
            db=db,
            memorial_id=memorial_id,
            memorial_update=memorial_update,
            user_id=current_user.id
        )
        
        if not memorial:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Memorial not found"
            )
        
        # Convert to response schema with explicit field mapping
        memorial_response = MemorialResponse(
            id=memorial.id,
            owner_id=memorial.owner_id,
            deceased_name_hebrew=memorial.deceased_name_hebrew,
            deceased_name_english=memorial.deceased_name_english,
            parent_name_hebrew=memorial.parent_name_hebrew,
            spouse_name=memorial.spouse_name,
            children_names=memorial.children_names,
            parents_names=memorial.parents_names,
            family_names=memorial.family_names,
            birth_date_gregorian=memorial.birth_date_gregorian,
            birth_date_hebrew=memorial.birth_date_hebrew,
            death_date_gregorian=memorial.death_date_gregorian,
            death_date_hebrew=memorial.death_date_hebrew,
            yahrzeit_date_hebrew=memorial.yahrzeit_date_hebrew,
            next_yahrzeit_gregorian=memorial.next_yahrzeit_gregorian,
            biography=memorial.biography,
            memorial_song_url=memorial.memorial_song_url,
            is_locked=memorial.is_locked,
            is_public=memorial.is_public,
            page_views=memorial.page_views,
            unique_slug=memorial.unique_slug,
            created_at=memorial.created_at,
            updated_at=memorial.updated_at,
            display_name=memorial.display_name,
            age_at_death=memorial.age_at_death,
            public_url=memorial.public_url,
            years_since_death=memorial.years_since_death
        )
        
        logger.info(f"Memorial {memorial_id} updated successfully: {changes}")
        
        return MemorialUpdateResponse(
            success=True,
            message="Memorial updated successfully",
            memorial=memorial_response,
            changes=changes
        )
        
    except MemorialNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Memorial not found"
        )
    except MemorialPermissionError as e:
        logger.warning(f"Memorial update permission denied: {e}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except MemorialValidationError as e:
        logger.warning(f"Memorial update validation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except MemorialError as e:
        logger.error(f"Memorial update failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update memorial"
        )
    except Exception as e:
        logger.error(f"Unexpected error during memorial update: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.delete(
    "/{memorial_id}",
    response_model=MemorialDeleteResponse,
    summary="Delete memorial",
    description="Delete memorial (soft delete by default)."
)
@limiter.limit("10/hour")  # Limit memorial deletions
async def delete_memorial(
    request: Request,
    memorial_id: Annotated[UUID, Path(..., description="Memorial ID")],
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_verified_user)],
    memorial_service: Annotated[MemorialService, Depends(get_memorial_service)],
    hard_delete: bool = Query(False, description="Permanently delete (admin only)")
) -> MemorialDeleteResponse:
    """
    Delete memorial.
    
    By default performs soft delete (can be restored).
    Hard delete is only available to administrators and is permanent.
    User must be the memorial owner or an administrator.
    """
    try:
        logger.info(f"Deleting memorial {memorial_id} for user {current_user.id}")
        
        success = await memorial_service.delete_memorial(
            db=db,
            memorial_id=memorial_id,
            user_id=current_user.id,
            hard_delete=hard_delete
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Memorial not found"
            )
        
        delete_type = "permanently deleted" if hard_delete else "deleted"
        logger.info(f"Memorial {memorial_id} {delete_type} successfully")
        
        return MemorialDeleteResponse(
            success=True,
            message=f"Memorial {delete_type} successfully",
            memorial_id=memorial_id,
            deleted_at=datetime.now()
        )
        
    except MemorialNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Memorial not found"
        )
    except MemorialPermissionError as e:
        logger.warning(f"Memorial deletion permission denied: {e}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except MemorialError as e:
        logger.error(f"Memorial deletion failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete memorial"
        )
    except Exception as e:
        logger.error(f"Unexpected error during memorial deletion: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


# Public Memorial Access

@router.get(
    "/{slug}/public",
    response_model=PublicMemorialResponse,
    summary="Get public memorial by slug",
    description="Get public memorial page by URL slug (no authentication required)."
)
async def get_public_memorial(
    slug: Annotated[str, Path(..., description="Memorial URL slug")],
    db: Annotated[AsyncSession, Depends(get_db)],
    memorial_service: Annotated[MemorialService, Depends(get_memorial_service)]
) -> PublicMemorialResponse:
    """
    Get public memorial by URL slug.
    
    This endpoint is public and doesn't require authentication.
    Only returns publicly visible memorial information.
    """
    try:
        logger.info(f"Getting public memorial by slug: {slug}")
        
        memorial = await memorial_service.get_memorial_by_slug(
            db=db,
            slug=slug,
            include_photos=True
        )
        
        if not memorial:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Memorial not found or not public"
            )
        
        logger.info(f"Public memorial {slug} retrieved successfully")
        return memorial
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        logger.error(f"Failed to get public memorial {slug}: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve memorial: {str(e)}"
        )


# Memorial Search

@router.post(
    "/search",
    response_model=MemorialSearchResponse,
    summary="Search memorials",
    description="Search memorials with advanced filtering options."
)
@limiter.limit("60/hour")  # Limit search requests
async def search_memorials(
    request: Request,
    search_params: MemorialSearchRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    memorial_service: Annotated[MemorialService, Depends(get_memorial_service)],
    current_user: Annotated[Optional[User], Depends(get_current_user)] = None,
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(20, ge=1, le=100, description="Maximum items to return")
) -> MemorialSearchResponse:
    """
    Search memorials with filtering.
    
    Available filters:
    - **query**: Text search in names and biography
    - **birth_year_from/to**: Birth year range
    - **death_year_from/to**: Death year range  
    - **has_photos**: Filter by photo presence
    - **is_public**: Filter by public visibility
    - **sort_by**: Sort field (created_at, updated_at, deceased_name_hebrew, etc.)
    - **sort_order**: Sort direction (asc, desc)
    
    Authentication is optional - unauthenticated users see only public memorials.
    """
    try:
        user_id = current_user.id if current_user else None
        logger.info(f"Searching memorials for user {user_id}")
        
        result = await memorial_service.search_memorials(
            db=db,
            search_params=search_params,
            user_id=user_id,
            skip=skip,
            limit=limit
        )
        
        logger.info(
            f"Memorial search completed: {len(result.items)} results "
            f"in {result.search_time_ms:.2f}ms"
        )
        return result
        
    except Exception as e:
        logger.error(f"Memorial search failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Search failed"
        )


# Memorial Statistics

@router.get(
    "/{memorial_id}/stats",
    response_model=MemorialStatsResponse,
    summary="Get memorial statistics",
    description="Get detailed statistics for a memorial (owner only)."
)
async def get_memorial_stats(
    memorial_id: Annotated[UUID, Path(..., description="Memorial ID")],
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_verified_user)],
    memorial_service: Annotated[MemorialService, Depends(get_memorial_service)]
) -> MemorialStatsResponse:
    """
    Get memorial statistics.
    
    Returns detailed analytics including:
    - Page views
    - Photo count
    - Contact count
    - Days since creation
    - Days until next yahrzeit
    
    Only memorial owner can access statistics.
    """
    try:
        logger.info(f"Getting stats for memorial {memorial_id}")
        
        stats = await memorial_service.get_memorial_stats(
            db=db,
            memorial_id=memorial_id,
            user_id=current_user.id
        )
        
        if not stats:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Memorial not found or access denied"
            )
        
        logger.info(f"Memorial stats retrieved for {memorial_id}")
        return stats
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get memorial stats {memorial_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve statistics"
        )


# Memorial Slug Management

@router.put(
    "/{memorial_id}/slug",
    response_model=MemorialSlugResponse,
    summary="Update memorial slug",
    description="Update the URL slug for a memorial."
)
@limiter.limit("10/hour")  # Limit slug updates
async def update_memorial_slug(
    request: Request,
    memorial_id: Annotated[UUID, Path(..., description="Memorial ID")],
    slug_request: MemorialSlugRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_verified_user)],
    memorial_service: Annotated[MemorialService, Depends(get_memorial_service)]
) -> MemorialSlugResponse:
    """
    Update memorial URL slug.
    
    Slug must be unique and follow URL-safe format (lowercase, numbers, hyphens).
    Only memorial owner can update the slug.
    """
    try:
        logger.info(f"Updating slug for memorial {memorial_id}")
        
        # Get current memorial to check old slug
        memorial = await memorial_service.get_memorial_by_id(
            db=db,
            memorial_id=memorial_id,
            user_id=current_user.id
        )
        
        if not memorial:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Memorial not found"
            )
        
        if memorial.owner_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only memorial owner can update slug"
            )
        
        old_slug = memorial.unique_slug
        
        new_slug = await memorial_service.update_memorial_slug(
            db=db,
            memorial_id=memorial_id,
            new_slug=slug_request.new_slug,
            user_id=current_user.id
        )
        
        if not new_slug:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Slug already exists or update failed"
            )
        
        public_url = f"/memorial/{new_slug}" if memorial.is_public else ""
        
        logger.info(f"Memorial slug updated: {old_slug} -> {new_slug}")
        
        return MemorialSlugResponse(
            memorial_id=memorial_id,
            old_slug=old_slug,
            new_slug=new_slug,
            updated_at=datetime.now()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update memorial slug {memorial_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update slug"
        )



@router.get("/public/{slug}", response_model=MemorialWithPhotos)
async def get_public_memorial(
    slug: Annotated[str, Path(..., description="Memorial unique slug")],
    db: Annotated[AsyncSession, Depends(get_db)],
    memorial_service: Annotated[MemorialService, Depends(get_memorial_service)]
) -> MemorialWithPhotos:
    """
    Get public memorial information by slug.
    
    Returns memorial data with embedded photos for public viewing.
    Memorial must be marked as public.
    """
    try:
        logger.info(f"Getting public memorial by slug: {slug}")
        
        # Get memorial by slug
        memorial_query = select(Memorial).where(
            Memorial.unique_slug == slug,
            Memorial.is_public == True,
            Memorial.is_deleted == False
        )
        result = await db.execute(memorial_query)
        memorial = result.scalar_one_or_none()
        
        if not memorial:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Memorial not found or not public"
            )
        
        # Get photos
        photos_query = select(Photo).where(
            Photo.memorial_id == memorial.id,
            Photo.is_approved == True
        ).order_by(Photo.display_order)
        
        photos_result = await db.execute(photos_query)
        photos = photos_result.scalars().all()
        
        # Convert photos to response format
        photo_responses = []
        for photo in photos:
            photo_responses.append(PhotoResponse(
                id=photo.id,
                memorial_id=photo.memorial_id,
                file_path=photo.file_path,
                file_url=photo.file_url,
                original_filename=photo.original_filename,
                photo_type=photo.photo_type,
                caption=photo.caption,
                display_order=photo.display_order,
                is_primary=photo.is_primary,
                is_approved=photo.is_approved,
                uploaded_at=photo.uploaded_at,
                created_at=photo.created_at,
                updated_at=photo.updated_at,
                display_name=photo.display_name,
                file_size=photo.file_size,
                mime_type=photo.mime_type,
                width=photo.width,
                height=photo.height,
                is_processed=photo.is_processed,
                processing_error=photo.processing_error,
                uploaded_by_user_id=photo.uploaded_by_user_id
            ))
        
        # Convert to dictionary and add photos
        memorial_dict = {
            'id': memorial.id,
            'owner_id': memorial.owner_id,
            'deceased_name_hebrew': memorial.deceased_name_hebrew,
            'deceased_name_english': memorial.deceased_name_english,
            'parent_name_hebrew': memorial.parent_name_hebrew,
            'spouse_name': memorial.spouse_name,
            'children_names': memorial.children_names,
            'parents_names': memorial.parents_names,
            'family_names': memorial.family_names,
            'birth_date_gregorian': memorial.birth_date_gregorian,
            'death_date_gregorian': memorial.death_date_gregorian,
            'birth_date_hebrew': memorial.birth_date_hebrew,
            'death_date_hebrew': memorial.death_date_hebrew,
            'biography': memorial.biography,
            'memorial_song_url': memorial.memorial_song_url,
            'is_public': memorial.is_public,
            'is_locked': memorial.is_locked,
            'enable_comments': memorial.enable_comments,
            'page_views': memorial.page_views,
            'unique_slug': memorial.unique_slug,
            'yahrzeit_date_hebrew': memorial.yahrzeit_date_hebrew,
            'next_yahrzeit_gregorian': memorial.next_yahrzeit_gregorian,
            'created_at': memorial.created_at,
            'updated_at': memorial.updated_at,
            'photos': photo_responses
        }
        
        response = MemorialWithPhotos(**memorial_dict)
        
        # Update page views
        memorial.page_views = (memorial.page_views or 0) + 1
        await db.commit()
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get public memorial {slug}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve memorial"
        )

# Error handlers would be registered at the FastAPI app level, not router level