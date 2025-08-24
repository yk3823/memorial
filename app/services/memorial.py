"""
Memorial service layer for Memorial Website.
Handles memorial CRUD operations, business logic, and Hebrew calendar integration.
"""

import logging
import re
import uuid
from datetime import date, datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple, Union
from uuid import UUID

from sqlalchemy import select, func, and_, or_, desc, asc, case
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy.exc import IntegrityError

from app.models.memorial import Memorial
from app.models.user import User, UserRole
from app.models.photo import Photo
from app.models.contact import Contact
from app.models.audit import AuditLog
from app.schemas.memorial_simple import (
    MemorialCreate,
    MemorialUpdate,
    MemorialResponse,
    PublicMemorialResponse,
    MemorialSearchRequest,
    MemorialSearchResponse,
    MemorialListResponse,
    MemorialStatsResponse
)
from app.services.hebrew_calendar import (
    HebrewCalendarService,
    get_hebrew_calendar_service,
    DateConversionError
)
from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class MemorialError(Exception):
    """Base exception for memorial operations."""
    pass


class MemorialNotFoundError(MemorialError):
    """Exception raised when memorial is not found."""
    pass


class MemorialPermissionError(MemorialError):
    """Exception raised when user lacks permission for memorial operation."""
    pass


class MemorialValidationError(MemorialError):
    """Exception raised when memorial data validation fails."""
    pass


class MemorialService:
    """
    Memorial service providing CRUD operations and business logic.
    
    This service handles:
    - Memorial creation, reading, updating, deletion
    - Permission validation and access control
    - Hebrew calendar integration for yahrzeit calculations
    - Slug generation and management
    - Photo association management
    - Search and filtering functionality
    - Analytics and statistics
    """
    
    def __init__(self):
        self.hebrew_calendar = get_hebrew_calendar_service()
    
    async def create_memorial(
        self,
        db: AsyncSession,
        memorial_data: MemorialCreate,
        owner_id: UUID
    ) -> Memorial:
        """
        Create a new memorial.
        
        Args:
            db: Database session
            memorial_data: Memorial creation data
            owner_id: ID of the memorial owner
            
        Returns:
            Memorial: Created memorial
            
        Raises:
            MemorialValidationError: If data validation fails
            MemorialError: If creation fails
        """
        try:
            logger.info(f"Creating memorial for user {owner_id}")
            
            # Create memorial instance with name transformation
            memorial = Memorial(
                owner_id=owner_id,
                deceased_name_hebrew=memorial_data.deceased_name_hebrew,  # Computed property from first+last names
                deceased_name_english=memorial_data.deceased_name_english,  # Computed property from first+last names
                parent_name_hebrew=memorial_data.parent_name_hebrew,
                birth_date_gregorian=memorial_data.birth_date_gregorian,
                birth_date_hebrew=memorial_data.birth_date_hebrew,
                death_date_gregorian=memorial_data.death_date_gregorian,
                death_date_hebrew=memorial_data.death_date_hebrew,
                biography=memorial_data.biography,
                memorial_song_url=str(memorial_data.memorial_song_url) if memorial_data.memorial_song_url else None,
                is_public=memorial_data.is_public
            )
            
            # Generate unique slug
            memorial.unique_slug = await self._generate_unique_slug(
                db,
                memorial_data.deceased_name_english or memorial_data.deceased_name_hebrew
            )
            
            # Calculate Hebrew calendar dates if provided
            await self._update_hebrew_calendar_data(memorial)
            
            # Add to database
            db.add(memorial)
            await db.commit()
            await db.refresh(memorial)
            
            # Log the creation
            await self._log_memorial_action(
                db,
                memorial.id,
                owner_id,
                "create",
                "Memorial created"
            )
            
            logger.info(f"Memorial created successfully: {memorial.id}")
            return memorial
            
        except IntegrityError as e:
            await db.rollback()
            logger.error(f"Memorial creation failed due to integrity error: {e}")
            raise MemorialValidationError("Memorial creation failed due to data constraint violation") from e
        except Exception as e:
            await db.rollback()
            logger.error(f"Memorial creation failed: {e}")
            raise MemorialError(f"Failed to create memorial: {e}") from e
    
    async def get_memorial_by_id(
        self,
        db: AsyncSession,
        memorial_id: UUID,
        user_id: Optional[UUID] = None,
        include_photos: bool = False
    ) -> Optional[Memorial]:
        """
        Get memorial by ID with access control.
        
        Args:
            db: Database session
            memorial_id: Memorial ID
            user_id: User ID for access control (None for public access)
            include_photos: Whether to load photos
            
        Returns:
            Optional[Memorial]: Memorial if found and accessible
        """
        try:
            # Build query with optional photo loading
            query = select(Memorial).where(Memorial.id == memorial_id)
            
            if include_photos:
                query = query.options(
                    selectinload(Memorial.photos),
                    selectinload(Memorial.owner)
                )
            
            result = await db.execute(query)
            memorial = result.scalar_one_or_none()
            
            if not memorial:
                return None
            
            # Check access permissions
            if not await self._can_access_memorial(memorial, user_id):
                return None
            
            # Increment page views for public access
            if user_id != memorial.owner_id and not memorial.is_locked:
                memorial.increment_page_views()
                await db.commit()
            
            return memorial
            
        except Exception as e:
            logger.error(f"Failed to get memorial {memorial_id}: {e}")
            return None
    
    async def get_memorial_by_slug(
        self,
        db: AsyncSession,
        slug: str,
        include_photos: bool = False
    ) -> Optional[PublicMemorialResponse]:
        """
        Get public memorial by slug.
        
        Args:
            db: Database session
            slug: Memorial slug
            include_photos: Whether to load photos
            
        Returns:
            Optional[PublicMemorialResponse]: Memorial response if found and public
        """
        try:
            query = (
                select(Memorial)
                .where(
                    and_(
                        Memorial.unique_slug == slug,
                        Memorial.is_public.is_(True),
                        Memorial.is_deleted.is_(False)
                    )
                )
            )
            
            # Eagerly load photos to avoid lazy loading issues
            if include_photos:
                query = query.options(selectinload(Memorial.photos))
            
            result = await db.execute(query)
            memorial = result.scalar_one_or_none()
            
            if not memorial:
                return None
            
            # Extract all data while session is active
            memorial_data = {
                "id": memorial.id,
                "owner_id": memorial.owner_id,
                "deceased_name_hebrew": memorial.deceased_name_hebrew,
                "deceased_name_english": memorial.deceased_name_english,
                "birth_date_gregorian": memorial.birth_date_gregorian,
                "birth_date_hebrew": memorial.birth_date_hebrew,
                "death_date_gregorian": memorial.death_date_gregorian,
                "death_date_hebrew": memorial.death_date_hebrew,
                "biography": memorial.biography,
                "memorial_song_url": memorial.memorial_song_url,
                "unique_slug": memorial.unique_slug,
                "yahrzeit_date_hebrew": memorial.yahrzeit_date_hebrew,
                "next_yahrzeit_gregorian": memorial.next_yahrzeit_gregorian,
                "page_views": memorial.page_views,
                "created_at": memorial.created_at,
                "updated_at": memorial.updated_at,
                "is_locked": memorial.is_locked,
                "is_public": memorial.is_public
            }
            
            # Compute display properties safely without accessing hybrid properties
            # display_name
            if memorial.deceased_name_english:
                memorial_data["display_name"] = f"{memorial.deceased_name_hebrew} ({memorial.deceased_name_english})"
            else:
                memorial_data["display_name"] = memorial.deceased_name_hebrew
            
            # age_at_death
            if memorial.birth_date_gregorian and memorial.death_date_gregorian:
                delta = memorial.death_date_gregorian - memorial.birth_date_gregorian
                memorial_data["age_at_death"] = delta.days // 365
            else:
                memorial_data["age_at_death"] = None
            
            # public_url
            if memorial.unique_slug and memorial.is_public:
                memorial_data["public_url"] = f"/memorial/{memorial.unique_slug}"
            else:
                memorial_data["public_url"] = None
            
            # years_since_death
            if memorial.death_date_gregorian:
                from datetime import date
                delta = date.today() - memorial.death_date_gregorian
                memorial_data["years_since_death"] = delta.days // 365
            else:
                memorial_data["years_since_death"] = None
            
            # Build photos list while session is active
            photos = []
            primary_photo = None
            if include_photos and memorial.photos:
                for photo in memorial.photos:
                    if not photo.is_deleted and photo.is_approved:
                        photo_dict = {
                            "id": photo.id,
                            "memorial_id": photo.memorial_id,
                            "filename": photo.original_filename,
                            "original_filename": photo.original_filename,
                            "file_path": photo.file_path,
                            "thumbnail_path": f"/storage/photos/thumbs/{photo.original_filename}",  # Simple path
                            "caption": photo.caption,
                            "is_primary": photo.is_primary,
                            "file_size": photo.file_size,
                            "width": photo.width,
                            "height": photo.height,
                            "mime_type": photo.mime_type,
                            "upload_date": photo.uploaded_at,
                            "is_deleted": photo.is_deleted,
                            "created_at": photo.created_at,
                            "updated_at": photo.updated_at
                        }
                        photos.append(photo_dict)
                        
                        # Set primary photo
                        if photo.is_primary:
                            primary_photo = photo_dict
            
            # Increment page views
            memorial.page_views = (memorial.page_views or 0) + 1
            memorial_data["page_views"] = memorial.page_views
            await db.commit()
            
            # Create the response after session operations are complete
            return PublicMemorialResponse(
                photos=photos,
                primary_photo=primary_photo,
                **memorial_data
            )
            
        except Exception as e:
            logger.error(f"Failed to get memorial by slug {slug}: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return None
    
    async def get_user_memorials(
        self,
        db: AsyncSession,
        user_id: UUID,
        skip: int = 0,
        limit: int = 20,
        include_photos: bool = False
    ) -> MemorialListResponse:
        """
        Get memorials owned by a user.
        
        Args:
            db: Database session
            user_id: User ID
            skip: Number of records to skip
            limit: Maximum number of records to return
            include_photos: Whether to load photos
            
        Returns:
            MemorialListResponse: Paginated list of memorials
        """
        try:
            # Count total memorials
            count_query = (
                select(func.count(Memorial.id))
                .where(
                    and_(
                        Memorial.owner_id == user_id,
                        Memorial.is_deleted.is_(False)
                    )
                )
            )
            
            count_result = await db.execute(count_query)
            total = count_result.scalar() or 0
            
            # Get memorials
            query = (
                select(Memorial)
                .where(
                    and_(
                        Memorial.owner_id == user_id,
                        Memorial.is_deleted.is_(False)
                    )
                )
                .order_by(desc(Memorial.created_at))
                .offset(skip)
                .limit(limit)
            )
            
            if include_photos:
                query = query.options(
                    selectinload(Memorial.photos)
                )
            
            result = await db.execute(query)
            memorials = result.scalars().all()
            
            # Convert to response schemas - avoid to_dict() to prevent sync access
            memorial_responses = []
            for memorial in memorials:
                # Manually create dict to avoid sync operations
                memorial_data = {
                    'id': memorial.id,
                    'owner_id': memorial.owner_id,  # Required field!
                    'deceased_name_hebrew': memorial.deceased_name_hebrew,
                    'deceased_name_english': memorial.deceased_name_english,
                    'parent_name_hebrew': memorial.parent_name_hebrew,  # Required field!
                    'birth_date_gregorian': memorial.birth_date_gregorian,
                    'death_date_gregorian': memorial.death_date_gregorian,
                    'birth_date_hebrew': memorial.birth_date_hebrew,
                    'death_date_hebrew': memorial.death_date_hebrew,
                    'yahrzeit_date_hebrew': memorial.yahrzeit_date_hebrew,
                    'next_yahrzeit_gregorian': memorial.next_yahrzeit_gregorian,
                    'biography': memorial.biography,
                    'memorial_song_url': memorial.memorial_song_url,
                    'is_public': memorial.is_public,
                    'is_locked': memorial.is_locked,
                    'enable_comments': memorial.enable_comments,
                    'location_lat': memorial.location_lat,
                    'location_lng': memorial.location_lng,
                    'whatsapp_phones': memorial.whatsapp_phones,
                    'notification_emails': memorial.notification_emails,
                    'unique_slug': memorial.unique_slug,
                    'page_views': memorial.page_views,
                    'created_at': memorial.created_at,
                    'updated_at': memorial.updated_at,
                    # Computed fields
                    'display_name': memorial.display_name,
                    'age_at_death': memorial.age_at_death,
                    'public_url': memorial.public_url,
                    'years_since_death': memorial.years_since_death,
                    # Safe defaults for counts
                    'photo_count': 0,
                    'contact_count': 0,
                    'primary_photo': None
                }
                memorial_responses.append(MemorialResponse(**memorial_data))
            
            return MemorialListResponse(
                items=memorial_responses,
                total=total,
                skip=skip,
                limit=limit,
                has_next=skip + limit < total,
                has_previous=skip > 0
            )
            
        except Exception as e:
            logger.error(f"Failed to get user memorials for {user_id}: {e}")
            return MemorialListResponse(
                items=[],
                total=0,
                skip=skip,
                limit=limit,
                has_next=False,
                has_previous=False
            )
    
    async def update_memorial(
        self,
        db: AsyncSession,
        memorial_id: UUID,
        memorial_update: MemorialUpdate,
        user_id: UUID
    ) -> Optional[Memorial]:
        """
        Update an existing memorial.
        
        Args:
            db: Database session
            memorial_id: Memorial ID to update
            memorial_update: Update data
            user_id: User performing the update
            
        Returns:
            Optional[Memorial]: Updated memorial if successful
            
        Raises:
            MemorialNotFoundError: If memorial not found
            MemorialPermissionError: If user lacks permission
            MemorialError: If update fails
        """
        try:
            # Get existing memorial
            memorial = await self.get_memorial_by_id(db, memorial_id, user_id)
            if not memorial:
                raise MemorialNotFoundError(f"Memorial {memorial_id} not found")
            
            # Check edit permissions
            if not memorial.can_be_edited_by(user_id):
                raise MemorialPermissionError("You don't have permission to edit this memorial")
            
            # Track changes
            changes = []
            
            # Update fields that are provided
            if memorial_update.deceased_name_hebrew is not None:
                if memorial_update.deceased_name_hebrew != memorial.deceased_name_hebrew:
                    memorial.deceased_name_hebrew = memorial_update.deceased_name_hebrew
                    changes.append("deceased_name_hebrew")
            
            if memorial_update.deceased_name_english is not None:
                if memorial_update.deceased_name_english != memorial.deceased_name_english:
                    memorial.deceased_name_english = memorial_update.deceased_name_english
                    changes.append("deceased_name_english")
                    
                    # Regenerate slug if English name changed
                    new_slug = await self._generate_unique_slug(
                        db,
                        memorial_update.deceased_name_english or memorial.deceased_name_hebrew,
                        exclude_memorial_id=memorial_id
                    )
                    memorial.unique_slug = new_slug
                    changes.append("unique_slug")
            
            if memorial_update.birth_date_gregorian is not None:
                if memorial_update.birth_date_gregorian != memorial.birth_date_gregorian:
                    memorial.birth_date_gregorian = memorial_update.birth_date_gregorian
                    changes.append("birth_date_gregorian")
            
            if memorial_update.birth_date_hebrew is not None:
                if memorial_update.birth_date_hebrew != memorial.birth_date_hebrew:
                    memorial.birth_date_hebrew = memorial_update.birth_date_hebrew
                    changes.append("birth_date_hebrew")
            
            if memorial_update.death_date_gregorian is not None:
                if memorial_update.death_date_gregorian != memorial.death_date_gregorian:
                    memorial.death_date_gregorian = memorial_update.death_date_gregorian
                    changes.append("death_date_gregorian")
                    # Recalculate yahrzeit if death date changed
                    await self._update_hebrew_calendar_data(memorial)
                    changes.append("yahrzeit_updated")
            
            if memorial_update.death_date_hebrew is not None:
                if memorial_update.death_date_hebrew != memorial.death_date_hebrew:
                    memorial.death_date_hebrew = memorial_update.death_date_hebrew
                    changes.append("death_date_hebrew")
                    # Recalculate yahrzeit if Hebrew death date changed
                    await self._update_hebrew_calendar_data(memorial)
                    changes.append("yahrzeit_updated")
            
            if memorial_update.biography is not None:
                if memorial_update.biography != memorial.biography:
                    memorial.biography = memorial_update.biography
                    changes.append("biography")
            
            if memorial_update.memorial_song_url is not None:
                song_url = str(memorial_update.memorial_song_url) if memorial_update.memorial_song_url else None
                if song_url != memorial.memorial_song_url:
                    memorial.memorial_song_url = song_url
                    changes.append("memorial_song_url")
            
            if memorial_update.is_public is not None:
                if memorial_update.is_public != memorial.is_public:
                    memorial.is_public = memorial_update.is_public
                    changes.append("is_public")
            
            # Only commit if there are changes
            if changes:
                await db.commit()
                await db.refresh(memorial)
                
                # Log the update
                await self._log_memorial_action(
                    db,
                    memorial.id,
                    user_id,
                    "update",
                    f"Memorial updated: {', '.join(changes)}"
                )
                
                logger.info(f"Memorial {memorial_id} updated by user {user_id}: {changes}")
            
            return memorial
            
        except (MemorialNotFoundError, MemorialPermissionError):
            raise
        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to update memorial {memorial_id}: {e}")
            raise MemorialError(f"Failed to update memorial: {e}") from e
    
    async def delete_memorial(
        self,
        db: AsyncSession,
        memorial_id: UUID,
        user_id: UUID,
        hard_delete: bool = False
    ) -> bool:
        """
        Delete a memorial (soft delete by default).
        
        Args:
            db: Database session
            memorial_id: Memorial ID to delete
            user_id: User performing the deletion
            hard_delete: Whether to permanently delete (admin only)
            
        Returns:
            bool: True if deleted successfully
            
        Raises:
            MemorialNotFoundError: If memorial not found
            MemorialPermissionError: If user lacks permission
            MemorialError: If deletion fails
        """
        try:
            # Get existing memorial
            memorial = await self.get_memorial_by_id(db, memorial_id, user_id)
            if not memorial:
                raise MemorialNotFoundError(f"Memorial {memorial_id} not found")
            
            # Check delete permissions
            # Only owner or admin can delete
            if memorial.owner_id != user_id:
                # Check if user is admin
                user_query = select(User).where(User.id == user_id)
                user_result = await db.execute(user_query)
                user = user_result.scalar_one_or_none()
                
                if not user or user.role != UserRole.ADMIN:
                    raise MemorialPermissionError("You don't have permission to delete this memorial")
            
            if hard_delete:
                # Hard delete (admin only)
                user_query = select(User).where(User.id == user_id)
                user_result = await db.execute(user_query)
                user = user_result.scalar_one_or_none()
                
                if not user or user.role != UserRole.ADMIN:
                    raise MemorialPermissionError("Only administrators can permanently delete memorials")
                
                await db.delete(memorial)
                logger.info(f"Memorial {memorial_id} permanently deleted by admin {user_id}")
            else:
                # Soft delete
                memorial.soft_delete()
                logger.info(f"Memorial {memorial_id} soft deleted by user {user_id}")
            
            # Log the deletion
            await self._log_memorial_action(
                db,
                memorial.id,
                user_id,
                "delete" if hard_delete else "soft_delete",
                "Memorial deleted" if hard_delete else "Memorial soft deleted"
            )
            
            await db.commit()
            return True
            
        except (MemorialNotFoundError, MemorialPermissionError):
            raise
        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to delete memorial {memorial_id}: {e}")
            raise MemorialError(f"Failed to delete memorial: {e}") from e
    
    async def search_memorials(
        self,
        db: AsyncSession,
        search_params: MemorialSearchRequest,
        user_id: Optional[UUID] = None,
        skip: int = 0,
        limit: int = 20
    ) -> MemorialSearchResponse:
        """
        Search memorials with filtering.
        
        Args:
            db: Database session
            search_params: Search parameters
            user_id: User ID for access control (None for public search)
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            MemorialSearchResponse: Search results
        """
        start_time = datetime.now()
        
        try:
            # Build base query
            query = select(Memorial).where(Memorial.is_deleted.is_(False))
            
            # Apply access control
            if user_id:
                # User can see their own memorials + public memorials
                query = query.where(
                    or_(
                        Memorial.owner_id == user_id,
                        Memorial.is_public.is_(True)
                    )
                )
            else:
                # Public search - only public memorials
                query = query.where(Memorial.is_public.is_(True))
            
            # Apply search filters
            filters_applied = {}
            
            if search_params.query:
                query_filter = or_(
                    Memorial.deceased_name_hebrew.ilike(f"%{search_params.query}%"),
                    Memorial.deceased_name_english.ilike(f"%{search_params.query}%"),
                    Memorial.biography.ilike(f"%{search_params.query}%")
                )
                query = query.where(query_filter)
                filters_applied["query"] = search_params.query
            
            if search_params.birth_year_from:
                query = query.where(
                    func.extract("year", Memorial.birth_date_gregorian) >= search_params.birth_year_from
                )
                filters_applied["birth_year_from"] = search_params.birth_year_from
            
            if search_params.birth_year_to:
                query = query.where(
                    func.extract("year", Memorial.birth_date_gregorian) <= search_params.birth_year_to
                )
                filters_applied["birth_year_to"] = search_params.birth_year_to
            
            if search_params.death_year_from:
                query = query.where(
                    func.extract("year", Memorial.death_date_gregorian) >= search_params.death_year_from
                )
                filters_applied["death_year_from"] = search_params.death_year_from
            
            if search_params.death_year_to:
                query = query.where(
                    func.extract("year", Memorial.death_date_gregorian) <= search_params.death_year_to
                )
                filters_applied["death_year_to"] = search_params.death_year_to
            
            if search_params.has_photos is not None:
                if search_params.has_photos:
                    query = query.join(Photo).where(Photo.is_deleted.is_(False))
                else:
                    # Memorials with no photos
                    subquery = (
                        select(Photo.memorial_id)
                        .where(Photo.is_deleted.is_(False))
                    )
                    query = query.where(~Memorial.id.in_(subquery))
                filters_applied["has_photos"] = search_params.has_photos
            
            if search_params.is_public is not None:
                query = query.where(Memorial.is_public.is_(search_params.is_public))
                filters_applied["is_public"] = search_params.is_public
            
            # Count total results
            count_query = select(func.count()).select_from(query.subquery())
            count_result = await db.execute(count_query)
            total = count_result.scalar() or 0
            
            # Apply sorting
            sort_column = getattr(Memorial, search_params.sort_by, Memorial.created_at)
            if search_params.sort_order == "asc":
                query = query.order_by(asc(sort_column))
            else:
                query = query.order_by(desc(sort_column))
            
            # Apply pagination
            query = query.offset(skip).limit(limit)
            
            # Execute query
            result = await db.execute(query)
            memorials = result.scalars().all()
            
            # Convert to response schemas
            memorial_responses = []
            for memorial in memorials:
                memorial_dict = memorial.to_dict()
                memorial_responses.append(MemorialResponse(**memorial_dict))
            
            # Calculate search time
            search_time_ms = (datetime.now() - start_time).total_seconds() * 1000
            
            return MemorialSearchResponse(
                items=memorial_responses,
                total=total,
                skip=skip,
                limit=limit,
                query=search_params.query,
                filters_applied=filters_applied,
                search_time_ms=search_time_ms
            )
            
        except Exception as e:
            logger.error(f"Memorial search failed: {e}")
            return MemorialSearchResponse(
                items=[],
                total=0,
                skip=skip,
                limit=limit,
                query=search_params.query,
                filters_applied={},
                search_time_ms=0
            )
    
    async def get_memorial_stats(
        self,
        db: AsyncSession,
        memorial_id: UUID,
        user_id: UUID
    ) -> Optional[MemorialStatsResponse]:
        """
        Get memorial statistics.
        
        Args:
            db: Database session
            memorial_id: Memorial ID
            user_id: User requesting stats (must be owner)
            
        Returns:
            Optional[MemorialStatsResponse]: Memorial statistics
        """
        try:
            # Get memorial with related data
            query = (
                select(Memorial)
                .options(
                    selectinload(Memorial.photos),
                    selectinload(Memorial.contacts),
                    selectinload(Memorial.notifications)
                )
                .where(Memorial.id == memorial_id)
            )
            
            result = await db.execute(query)
            memorial = result.scalar_one_or_none()
            
            if not memorial or memorial.owner_id != user_id:
                return None
            
            # Calculate days since creation
            days_since_created = (datetime.now() - memorial.created_at).days
            
            # Calculate days until next yahrzeit
            next_yahrzeit_days = None
            if memorial.next_yahrzeit_gregorian:
                days_until = (memorial.next_yahrzeit_gregorian - date.today()).days
                next_yahrzeit_days = max(0, days_until)
            
            return MemorialStatsResponse(
                id=memorial.id,
                page_views=memorial.page_views,
                photo_count=len([p for p in memorial.photos if not p.is_deleted]),
                contact_count=len([c for c in memorial.contacts if not c.is_deleted]),
                notification_count=len(memorial.notifications),
                days_since_created=days_since_created,
                next_yahrzeit_days=next_yahrzeit_days,
                last_updated=memorial.updated_at
            )
            
        except Exception as e:
            logger.error(f"Failed to get memorial stats for {memorial_id}: {e}")
            return None
    
    async def update_memorial_slug(
        self,
        db: AsyncSession,
        memorial_id: UUID,
        new_slug: str,
        user_id: UUID
    ) -> Optional[str]:
        """
        Update memorial slug.
        
        Args:
            db: Database session
            memorial_id: Memorial ID
            new_slug: New slug
            user_id: User performing update
            
        Returns:
            Optional[str]: New slug if successful
        """
        try:
            memorial = await self.get_memorial_by_id(db, memorial_id, user_id)
            if not memorial or memorial.owner_id != user_id:
                return None
            
            # Check if slug is unique
            if not await self._is_slug_unique(db, new_slug, memorial_id):
                raise MemorialValidationError("Slug already exists")
            
            memorial.unique_slug = new_slug
            await db.commit()
            
            return new_slug
            
        except Exception as e:
            logger.error(f"Failed to update memorial slug: {e}")
            return None
    
    # Private helper methods
    
    async def _generate_unique_slug(
        self,
        db: AsyncSession,
        name: str,
        exclude_memorial_id: Optional[UUID] = None
    ) -> str:
        """
        Generate unique slug from memorial name.
        
        Args:
            db: Database session
            name: Memorial name to base slug on
            exclude_memorial_id: Memorial ID to exclude from uniqueness check
            
        Returns:
            str: Unique slug
        """
        # Create base slug from name
        base_slug = self._slugify(name)
        
        # Ensure base slug is not empty
        if not base_slug:
            base_slug = "memorial"
        
        # Check uniqueness and append number if needed
        slug = base_slug
        counter = 1
        
        while not await self._is_slug_unique(db, slug, exclude_memorial_id):
            slug = f"{base_slug}-{counter}"
            counter += 1
            
            # Prevent infinite loop
            if counter > 9999:
                slug = f"{base_slug}-{uuid.uuid4().hex[:8]}"
                break
        
        return slug[:50]  # Limit length
    
    def _slugify(self, text: str) -> str:
        """
        Convert text to URL-safe slug.
        
        Args:
            text: Text to slugify
            
        Returns:
            str: URL-safe slug
        """
        if not text:
            return ""
        
        # Convert to lowercase
        text = text.lower()
        
        # Replace spaces and special characters with hyphens
        text = re.sub(r'[^a-z0-9]+', '-', text)
        
        # Remove leading/trailing hyphens
        text = text.strip('-')
        
        return text
    
    async def _is_slug_unique(
        self,
        db: AsyncSession,
        slug: str,
        exclude_memorial_id: Optional[UUID] = None
    ) -> bool:
        """
        Check if slug is unique.
        
        Args:
            db: Database session
            slug: Slug to check
            exclude_memorial_id: Memorial ID to exclude from check
            
        Returns:
            bool: True if unique
        """
        query = select(Memorial).where(
            and_(
                Memorial.unique_slug == slug,
                Memorial.is_deleted.is_(False)
            )
        )
        
        if exclude_memorial_id:
            query = query.where(Memorial.id != exclude_memorial_id)
        
        result = await db.execute(query)
        existing = result.scalar_one_or_none()
        
        return existing is None
    
    async def _can_access_memorial(
        self,
        memorial: Memorial,
        user_id: Optional[UUID]
    ) -> bool:
        """
        Check if user can access memorial.
        
        Args:
            memorial: Memorial to check
            user_id: User ID (None for public access)
            
        Returns:
            bool: True if accessible
        """
        # Soft deleted memorials are not accessible
        if memorial.is_deleted:
            return False
        
        # Owner can always access
        if user_id and memorial.owner_id == user_id:
            return True
        
        # Public memorials are accessible to all
        if memorial.is_public:
            return True
        
        # Private memorials are only accessible to owner
        return False
    
    async def _update_hebrew_calendar_data(self, memorial: Memorial):
        """
        Update Hebrew calendar data for memorial.
        
        Args:
            memorial: Memorial to update
        """
        try:
            async with self.hebrew_calendar:
                # Convert death date to Hebrew if Gregorian is provided
                if memorial.death_date_gregorian and not memorial.death_date_hebrew:
                    hebrew_date = await self.hebrew_calendar.gregorian_to_hebrew(
                        memorial.death_date_gregorian
                    )
                    memorial.death_date_hebrew = self.hebrew_calendar.format_hebrew_date(hebrew_date)
                
                # Calculate yahrzeit if Hebrew death date is available
                if memorial.death_date_hebrew:
                    yahrzeit_hebrew = await self.hebrew_calendar.calculate_yahrzeit_date(
                        memorial.death_date_hebrew
                    )
                    memorial.yahrzeit_date_hebrew = self.hebrew_calendar.format_hebrew_date(yahrzeit_hebrew)
                    
                    # Calculate next yahrzeit in Gregorian calendar
                    next_yahrzeit_gregorian, _ = await self.hebrew_calendar.get_next_yahrzeit(
                        memorial.death_date_hebrew
                    )
                    memorial.next_yahrzeit_gregorian = next_yahrzeit_gregorian
        
        except DateConversionError as e:
            logger.warning(f"Hebrew calendar conversion failed for memorial: {e}")
        except Exception as e:
            logger.error(f"Failed to update Hebrew calendar data: {e}")
    
    async def _log_memorial_action(
        self,
        db: AsyncSession,
        memorial_id: UUID,
        user_id: UUID,
        action: str,
        description: str
    ):
        """
        Log memorial action to audit trail.
        
        Args:
            db: Database session
            memorial_id: Memorial ID
            user_id: User ID
            action: Action performed
            description: Action description
        """
        try:
            audit_log = AuditLog(
                user_id=user_id,
                resource_type="memorial",
                resource_id=str(memorial_id),
                action=action,
                description=description,
                ip_address=None,  # Would be populated by API layer
                user_agent=None   # Would be populated by API layer
            )
            
            db.add(audit_log)
            # Note: commit is handled by calling method
        
        except Exception as e:
            logger.error(f"Failed to log memorial action: {e}")


# Global service instance
_memorial_service: Optional[MemorialService] = None


def get_memorial_service() -> MemorialService:
    """
    Get memorial service singleton.
    
    Returns:
        MemorialService: Service instance
    """
    global _memorial_service
    if _memorial_service is None:
        _memorial_service = MemorialService()
    return _memorial_service