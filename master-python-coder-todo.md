# Memorial Website - Master Python Coder Implementation TODO

This document provides a detailed, step-by-step implementation plan for the master-python-coder agent to build a fully functional, production-ready Memorial Website.

## 🚨 CRITICAL PRIORITY - Phase 1: Bug Fixes (Day 1)

### **1.1 Fix SQLAlchemy Async Serialization Bug**
- **File**: `/Users/josephkeinan/memorial/app/api/v1/memorial.py`
- **Issue**: Memorial creation returns HTTP 500 despite successful database save
- **Error**: `greenlet_spawn has not been called; can't call await_only() here`
- **Location**: Lines 111-113 in `create_memorial` function

**Implementation Steps:**
```python
# Fix the memorial response creation
# Replace:
memorial_response = MemorialResponse(**memorial.to_dict())

# With explicit field mapping:
memorial_response = MemorialResponse(
    id=memorial.id,
    owner_id=memorial.owner_id,
    deceased_name_hebrew=memorial.deceased_name_hebrew,
    deceased_name_english=memorial.deceased_name_english,
    death_date_gregorian=memorial.death_date_gregorian,
    death_date_hebrew=memorial.death_date_hebrew,
    yahrzeit_date_hebrew=memorial.yahrzeit_date_hebrew,
    next_yahrzeit_gregorian=memorial.next_yahrzeit_gregorian,
    biography=memorial.biography,
    is_public=memorial.is_public,
    slug=memorial.slug,
    created_at=memorial.created_at,
    updated_at=memorial.updated_at
)
```

**Update Memorial Model:**
- **File**: `/Users/josephkeinan/memorial/app/models/memorial.py`
- Remove async calls from `to_dict()` method
- Add computed properties without database queries

**Test**: Verify memorial creation returns HTTP 201 with proper JSON response

---

## 📸 PHASE 2: Photo Upload System (Days 2-4)

### **2.1 Photo Upload API Implementation**
- **File**: `/Users/josephkeinan/memorial/app/api/v1/photos.py` (CREATE NEW)

**Required Endpoints:**
```python
@router.post("/memorials/{memorial_id}/photos")
async def upload_photos(
    memorial_id: UUID,
    files: List[UploadFile] = File(...),
    photo_types: List[str] = Form(...),
    current_user: User = Depends(get_current_verified_user)
):
    """Upload up to 6 photos for a memorial"""
    # Validate: 1 deceased (required), 1 grave (optional), 4 additional (optional)
    # Process each photo type: deceased, grave, memorial1, memorial2, memorial3, memorial4
    pass

@router.delete("/photos/{photo_id}")
async def delete_photo():
    """Delete a specific photo"""
    pass

@router.put("/photos/{photo_id}/reorder")  
async def reorder_photos():
    """Change photo display order"""
    pass
```

### **2.2 Photo Processing Service**
- **File**: `/Users/josephkeinan/memorial/app/services/photo.py` (ENHANCE EXISTING)

**Implementation Requirements:**
```python
class PhotoService:
    async def process_uploaded_photo(self, file: UploadFile, photo_type: str, memorial_id: UUID):
        """Process and store uploaded photo"""
        # 1. Validate file (JPG, PNG, WebP, max 10MB)
        # 2. Generate secure filename with UUID
        # 3. Resize image: 1920x1080 (display), 400x400 (thumbnail)
        # 4. Save to /uploads/images/{memorial_id}/
        # 5. Store metadata in database
        # 6. Return photo record
        
    async def generate_thumbnails(self, image_path: str):
        """Generate multiple image sizes"""
        # Create: thumbnail (400x400), medium (800x600), large (1920x1080)
        
    def validate_photo_limits(self, memorial_id: UUID, photo_type: str):
        """Validate photo upload limits"""
        # deceased: max 1, grave: max 1, memorial: max 4
```

### **2.3 Photo Upload Frontend Component**
- **File**: `/Users/josephkeinan/memorial/app/templates/memorial/components/photo_upload.html` (CREATE NEW)

**Required Features:**
- Drag-and-drop photo upload interface
- Photo type selection (deceased, grave, memorial)
- Preview thumbnails with delete option
- Upload progress indicators
- Hebrew/English labels with RTL support

---

## 📅 PHASE 3: Hebrew Calendar Integration (Days 5-6)

### **3.1 Hebrew Calendar Service Enhancement**
- **File**: `/Users/josephkeinan/memorial/app/services/hebrew_calendar.py` (ENHANCE EXISTING)

**Required Methods:**
```python
class HebrewCalendarService:
    def calculate_yahrzeit(self, death_date_hebrew: str) -> Tuple[str, date]:
        """Calculate yahrzeit (11 months after death in Hebrew calendar)"""
        # Parse Hebrew date string
        # Add 11 Hebrew months using Hebcal API or local calculation
        # Handle Hebrew leap years
        # Return Hebrew yahrzeit date and next Gregorian occurrence
        
    def get_next_yahrzeit_gregorian(self, yahrzeit_hebrew: str) -> date:
        """Get next yahrzeit occurrence in Gregorian calendar"""
        # Convert Hebrew yahrzeit to next Gregorian date
        # Handle year conversions and leap year adjustments
        
    def convert_gregorian_to_hebrew(self, gregorian_date: date) -> str:
        """Convert Gregorian date to Hebrew calendar"""
        # Use Hebcal API: https://www.hebcal.com/converter
        
    def is_yahrzeit_approaching(self, next_yahrzeit: date, days_ahead: int = 14) -> bool:
        """Check if yahrzeit is within specified days"""
```

### **3.2 Memorial Service Integration**
- **File**: `/Users/josephkeinan/memorial/app/services/memorial.py` (UPDATE EXISTING)

**Add Yahrzeit Calculation:**
```python
async def create_memorial(self, memorial_data: MemorialCreate, owner_id: UUID):
    # Existing memorial creation code...
    
    # Add Hebrew calendar processing
    if memorial.death_date_gregorian:
        hebrew_death_date = await self.hebrew_calendar.convert_gregorian_to_hebrew(
            memorial.death_date_gregorian
        )
        yahrzeit_hebrew, next_yahrzeit = await self.hebrew_calendar.calculate_yahrzeit(
            hebrew_death_date
        )
        memorial.death_date_hebrew = hebrew_death_date
        memorial.yahrzeit_date_hebrew = yahrzeit_hebrew
        memorial.next_yahrzeit_gregorian = next_yahrzeit
```

---

## 📧 PHASE 4: Email Notification System (Days 7-9)

### **4.1 Email Service Enhancement**
- **File**: `/Users/josephkeinan/memorial/app/services/email.py` (ENHANCE EXISTING)

**Required Email Types:**
```python
class EmailService:
    async def send_yahrzeit_reminder(self, memorial: Memorial, contacts: List[Contact]):
        """Send yahrzeit reminder 2 weeks before"""
        # Create Hebrew/English email template
        # Include memorial page link
        # Send to up to 5 email contacts
        
    async def send_memorial_created_notification(self, memorial: Memorial):
        """Notify when memorial page is created"""
        
    async def send_memorial_updated_notification(self, memorial: Memorial):
        """Notify when memorial content is updated"""
        
    async def schedule_yahrzeit_notifications(self, memorial_id: UUID):
        """Schedule automatic yahrzeit reminders"""
        # Calculate notification date (14 days before yahrzeit)
        # Create background job for email sending
```

### **4.2 Email Templates**
- **Files**: 
  - `/Users/josephkeinan/memorial/app/templates/email/yahrzeit_reminder_he.html` (CREATE NEW)
  - `/Users/josephkeinan/memorial/app/templates/email/yahrzeit_reminder_en.html` (CREATE NEW)

**Hebrew Email Template:**
```html
<div dir="rtl" style="font-family: 'Noto Sans Hebrew', Arial;">
    <h2>🕯️ תזכורת יארצייט</h2>
    <p>שלום,</p>
    <p>יארצייט של <strong>{{ memorial.deceased_name_hebrew }}</strong> יחול בתאריך <strong>{{ memorial.next_yahrzeit_gregorian }}</strong></p>
    <p>לצפייה בדף הזיכרון: <a href="{{ memorial.public_url }}">{{ memorial.public_url }}</a></p>
    <p>תהא נשמתו צרורה בצרור החיים</p>
</div>
```

### **4.3 Background Job Scheduler**
- **File**: `/Users/josephkeinan/memorial/app/services/scheduler.py` (CREATE NEW)

**Daily Notification Check:**
```python
import asyncio
from datetime import date, timedelta

async def check_upcoming_yahrzeits():
    """Daily task to check and send yahrzeit notifications"""
    # Query memorials with yahrzeit in 14 days
    # Send reminder emails to notification contacts
    # Log notification delivery status
    
async def schedule_daily_notifications():
    """Background scheduler for notification system"""
    while True:
        await check_upcoming_yahrzeits()
        await asyncio.sleep(24 * 3600)  # Run daily
```

---

## 🎨 PHASE 5: Complete Frontend Templates (Days 10-14)

### **5.1 Memorial Setup Page**
- **File**: `/Users/josephkeinan/memorial/app/templates/memorial/setup.html` (CREATE NEW)

**Required Sections:**
1. **Personal Information**
   - Hebrew name (required) with Hebrew input validation
   - English name (optional)
   - Birth and death dates with Hebrew calendar display
   - 3 text blocks for biography/memories/tributes

2. **Photo Upload Section**
   - Primary deceased photo (required)
   - Grave photo (optional)
   - 4 additional memorial photos (optional)
   - Drag-and-drop interface with previews

3. **Location Management**
   - Cemetery name and address
   - GPS coordinate capture (mobile geolocation)
   - Section/plot number
   - Map preview with markers

4. **Video Upload**
   - Grave directions video (optional, max 100MB)
   - Video preview and processing status

5. **Notification Contacts**
   - Up to 5 email addresses
   - Contact relationship (son, daughter, spouse, etc.)
   - Notification preferences

6. **WhatsApp Group Setup**
   - Group creation button
   - Member phone numbers (up to 5)
   - Custom welcome message

### **5.2 Public Memorial Page**
- **File**: `/Users/josephkeinan/memorial/app/templates/memorial/public.html` (ENHANCE EXISTING)

**Required Features:**
```html
<div class="memorial-page" dir="rtl">
    <!-- Header with Hebrew/English names -->
    <header class="memorial-header">
        <h1>{{ memorial.deceased_name_hebrew }}</h1>
        <h2>{{ memorial.deceased_name_english }}</h2>
        <p class="dates">{{ memorial.birth_date }} - {{ memorial.death_date }}</p>
    </header>
    
    <!-- Primary photo display -->
    <div class="primary-photo">
        <img src="{{ memorial.primary_photo.url }}" alt="תמונה ראשית">
    </div>
    
    <!-- Photo gallery with lightbox -->
    <div class="photo-gallery">
        <!-- All memorial photos with modal popup -->
    </div>
    
    <!-- Biography sections -->
    <div class="biography">
        <!-- 3 text blocks with Hebrew formatting -->
    </div>
    
    <!-- Yahrzeit information -->
    <div class="yahrzeit-info">
        <h3>יארצייט</h3>
        <p>יארציית הבא: {{ memorial.next_yahrzeit_gregorian }}</p>
    </div>
    
    <!-- Location with map -->
    <div class="location-section">
        <div id="cemetery-map"></div>
        <div class="directions">
            <a href="{{ google_maps_url }}">Google Maps</a>
            <a href="{{ waze_url }}">Waze</a>
            <a href="{{ apple_maps_url }}">Apple Maps</a>
        </div>
    </div>
    
    <!-- Directions video -->
    {% if memorial.directions_video %}
    <div class="directions-video">
        <video controls>
            <source src="{{ memorial.directions_video.url }}" type="video/mp4">
        </video>
    </div>
    {% endif %}
</div>
```

### **5.3 Navigation and Layout Components**
- **File**: `/Users/josephkeinan/memorial/app/templates/components/navbar.html` (ENHANCE EXISTING)

**Features:**
- Hebrew/English language toggle
- User authentication status
- Memorial management links
- Search functionality
- Mobile-responsive hamburger menu

---

## 📱 PHASE 6: WhatsApp Integration (Days 15-17)

### **6.1 WhatsApp Business API Service**
- **File**: `/Users/josephkeinan/memorial/app/services/whatsapp.py` (CREATE NEW)

```python
class WhatsAppService:
    def __init__(self):
        self.access_token = settings.WHATSAPP_ACCESS_TOKEN
        self.phone_number_id = settings.WHATSAPP_PHONE_NUMBER_ID
        
    async def create_memorial_group(self, memorial: Memorial, phone_numbers: List[str]):
        """Create WhatsApp group for memorial family"""
        group_name = f"זיכרון {memorial.deceased_name_hebrew}"
        
        # Create group using WhatsApp Business API
        group_data = await self._create_group(group_name, phone_numbers)
        
        # Send welcome message
        welcome_message = f"""
🕯️ ברוכים הבאים לקבוצת הזיכרון של {memorial.deceased_name_hebrew}

דף הזיכרון: {memorial.public_url}

תקבלו התראות לפני יארצייט.
        """
        await self._send_group_message(group_data['id'], welcome_message)
        
        return group_data['id']
        
    async def send_yahrzeit_reminder_to_group(self, group_id: str, memorial: Memorial):
        """Send yahrzeit reminder to WhatsApp group"""
        message = f"""
🕯️ תזכורת יארצייט

יארצייט של {memorial.deceased_name_hebrew} יחול בעוד שבועיים
📅 תאריך: {memorial.next_yahrzeit_gregorian}

לדף הזיכרון: {memorial.public_url}

תהא נשמתו צרורה בצרור החיים
        """
        await self._send_group_message(group_id, message)
```

### **6.2 WhatsApp Group API Endpoints**
- **File**: `/Users/josephkeinan/memorial/app/api/v1/whatsapp.py` (CREATE NEW)

```python
@router.post("/memorials/{memorial_id}/whatsapp-group")
async def create_whatsapp_group(
    memorial_id: UUID,
    group_request: WhatsAppGroupRequest,
    current_user: User = Depends(get_current_verified_user)
):
    """Create WhatsApp group for memorial notifications"""
    # Validate phone numbers (up to 5)
    # Create WhatsApp group
    # Store group info in database
    # Return group creation status
```

---

## 📍 PHASE 7: GPS and Location Management (Days 18-19)

### **7.1 Location Service**
- **File**: `/Users/josephkeinan/memorial/app/services/location.py` (CREATE NEW)

```python
class LocationService:
    def __init__(self):
        self.google_maps_key = settings.GOOGLE_MAPS_API_KEY
        
    async def geocode_cemetery_address(self, address: str) -> Tuple[float, float]:
        """Convert cemetery address to GPS coordinates"""
        # Use Google Geocoding API
        # Return latitude, longitude
        
    def generate_directions_urls(self, lat: float, lng: float) -> Dict[str, str]:
        """Generate directions URLs for different map providers"""
        return {
            'google': f"https://maps.google.com/maps?q={lat},{lng}&navigate=yes",
            'waze': f"https://waze.com/ul?ll={lat},{lng}&navigate=yes", 
            'apple': f"https://maps.apple.com/maps?q={lat},{lng}&dirflg=d"
        }
```

### **7.2 Location Input Component**
- **File**: `/Users/josephkeinan/memorial/app/templates/memorial/components/location_input.html` (CREATE NEW)

**Features:**
- Cemetery name and address input
- GPS coordinate capture using geolocation API
- Map preview with marker
- Section/plot number fields
- Directions link generation

---

## 🎥 PHASE 8: Video Upload System (Days 20-21)

### **8.1 Video Processing Service**
- **File**: `/Users/josephkeinan/memorial/app/services/video.py` (CREATE NEW)

```python
class VideoService:
    async def process_directions_video(self, video_file: UploadFile, memorial_id: UUID):
        """Process uploaded directions video"""
        # 1. Validate video file (MP4, MOV, max 100MB)
        # 2. Generate secure filename
        # 3. Compress video using FFmpeg (720p, optimized for web)
        # 4. Generate thumbnail at 2-second mark
        # 5. Store in /uploads/videos/{memorial_id}/
        # 6. Update database with video metadata
        
    async def generate_video_thumbnail(self, video_path: str) -> str:
        """Generate video thumbnail using FFmpeg"""
        # Extract frame at 2 seconds
        # Save as JPEG thumbnail
        # Return thumbnail path
```

### **8.2 Video Upload API**
- **File**: `/Users/josephkeinan/memorial/app/api/v1/videos.py` (CREATE NEW)

```python
@router.post("/memorials/{memorial_id}/directions-video")
async def upload_directions_video(
    memorial_id: UUID,
    video: UploadFile = File(...),
    current_user: User = Depends(get_current_verified_user)
):
    """Upload directions video for grave location"""
    # Validate memorial ownership
    # Process video file
    # Return upload status and video info
```

---

## 🔍 PHASE 9: Site-Wide Search (Days 22-23)

### **9.1 Search Service Implementation**
- **File**: `/Users/josephkeinan/memorial/app/services/search.py` (CREATE NEW)

```python
class SearchService:
    async def search_memorials(self, query: str, filters: Dict = None) -> List[Memorial]:
        """Search memorials by name, biography, or other content"""
        # PostgreSQL full-text search
        # Search deceased_name_hebrew, deceased_name_english, biography
        # Return ranked results with highlighting
        
    async def index_memorial_for_search(self, memorial: Memorial):
        """Index memorial content for search"""
        # Update search vector in database
        # Include Hebrew and English names, biography text
```

### **9.2 Search API and Frontend**
- **File**: `/Users/josephkeinan/memorial/app/api/v1/search.py` (CREATE NEW)
- **File**: `/Users/josephkeinan/memorial/app/templates/search/results.html` (CREATE NEW)

**Search Results Features:**
- Search by Hebrew or English names
- Results with photo thumbnails
- Pagination with 20 results per page
- Search filters (year range, location)
- Hebrew/English result display

---

## ✅ PHASE 10: Testing and Quality Assurance (Days 24-26)

### **10.1 Unit Testing**
- **Directory**: `/Users/josephkeinan/memorial/tests/unit/`

**Required Test Files:**
```
tests/unit/
├── test_memorial_service.py      # Memorial creation, update, delete
├── test_photo_service.py         # Photo upload, processing, validation
├── test_hebrew_calendar.py       # Yahrzeit calculations, date conversions
├── test_email_service.py         # Email notifications, templates
├── test_whatsapp_service.py      # WhatsApp group creation, messaging
├── test_location_service.py      # GPS, geocoding, directions
├── test_video_service.py         # Video upload, processing
└── test_search_service.py        # Search functionality, indexing
```

### **10.2 Integration Testing**
- **Directory**: `/Users/josephkeinan/memorial/tests/integration/`

**Test Complete Workflows:**
- User registration → Memorial creation → Photo upload → Public page
- Memorial setup → Email notifications → WhatsApp group creation
- Search functionality → Result display → Memorial page access

### **10.3 End-to-End Testing**
- **File**: `/Users/josephkeinan/memorial/tests/e2e/test_complete_journey.py`

**Test Full User Journey:**
1. User registration and login
2. Memorial setup page completion
3. Photo upload (all 6 types)
4. Location and video upload
5. Email contact setup
6. WhatsApp group creation
7. Public memorial page verification
8. Search functionality testing

---

## 🛡️ PHASE 11: Security and Performance (Days 27-28)

### **11.1 Security Implementation**
- **File**: `/Users/josephkeinan/memorial/app/core/security.py` (ENHANCE EXISTING)

**Required Security Features:**
```python
# File upload validation
def validate_uploaded_file(file: UploadFile, file_type: str) -> bool:
    """Validate uploaded file for security"""
    # Check file extension and MIME type
    # Validate file headers
    # Scan for malicious content
    # Check file size limits
    
# Rate limiting
@limiter.limit("5/hour")  # Photo uploads
@limiter.limit("3/hour")  # Memorial creation
@limiter.limit("100/hour")  # Search requests

# Input sanitization
def sanitize_hebrew_input(text: str) -> str:
    """Sanitize Hebrew text input"""
    # Remove dangerous characters
    # Validate Hebrew character encoding
    # Prevent XSS attacks
```

### **11.2 Performance Optimization**
- **Database Indexes**: Add critical indexes for search, filtering, and sorting
- **Caching**: Implement Redis caching for frequently accessed data
- **Image Optimization**: Compress images and generate multiple sizes
- **Query Optimization**: Optimize database queries with proper joins and pagination

---

## 🚀 PHASE 12: Production Deployment (Days 29-30)

### **12.1 Environment Configuration**
- **File**: `/Users/josephkeinan/memorial/app/core/config.py` (UPDATE EXISTING)

**Add Production Settings:**
```python
# File storage
UPLOAD_DIR: str = "/app/uploads"
MAX_IMAGE_SIZE: int = 10 * 1024 * 1024  # 10MB
MAX_VIDEO_SIZE: int = 100 * 1024 * 1024  # 100MB

# External APIs
GOOGLE_MAPS_API_KEY: str = ""
WHATSAPP_ACCESS_TOKEN: str = ""
HEBREW_CALENDAR_API_URL: str = "https://www.hebcal.com/converter"

# Email service
SMTP_HOST: str = "smtp.gmail.com"
SMTP_PORT: int = 587
SMTP_USER: str = ""
SMTP_PASSWORD: str = ""
```

### **12.2 Docker Configuration**
- **File**: `/Users/josephkeinan/memorial/Dockerfile` (UPDATE EXISTING)

**Add Production Dependencies:**
```dockerfile
# Install FFmpeg for video processing
RUN apt-get update && apt-get install -y \
    ffmpeg \
    imagemagick \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Create uploads directory structure
RUN mkdir -p /app/uploads/images /app/uploads/videos /app/uploads/temp
```

---

## 📋 Implementation Checklist

### **Critical Bugs (Must Fix First)**
- [ ] Fix SQLAlchemy async serialization in memorial creation
- [ ] Implement proper error handling for 401/404 responses
- [ ] Verify memorial creation returns HTTP 201 with complete data

### **Core Features (MVP)**
- [ ] Photo upload system (6 photos: deceased, grave, 4 additional)
- [ ] Hebrew calendar yahrzeit calculation (11 months after death)
- [ ] Email notification system (5 contacts, 2 weeks before yahrzeit)
- [ ] Complete memorial setup page with all sections
- [ ] Public memorial page with photo gallery and information
- [ ] Site-wide search functionality by deceased name

### **Advanced Features**
- [ ] WhatsApp Business API integration (group creation, 5 members)
- [ ] GPS location management with map integration
- [ ] Video upload and processing for grave directions
- [ ] Automated background job scheduler for notifications
- [ ] Mobile-responsive design with Hebrew RTL support

### **Production Readiness**
- [ ] Comprehensive test suite (unit, integration, e2e)
- [ ] Security validation (file upload, input sanitization)
- [ ] Performance optimization (caching, indexes, compression)
- [ ] Production deployment configuration
- [ ] Monitoring and logging setup

---

## 🎯 Success Criteria

### **Technical Success Metrics**
- All API endpoints return correct HTTP status codes (100% success rate)
- Memorial creation completes successfully with all data saved
- Photo upload processing time under 30 seconds
- Search response time under 200ms
- Page load time under 2 seconds on mobile

### **Functional Requirements**
- Users can create complete memorial pages with all 6 photo types
- Hebrew calendar yahrzeit calculations are accurate and reliable
- Email notifications are delivered 2 weeks before yahrzeit dates
- WhatsApp groups are created successfully with custom messages
- Public memorial pages are searchable by deceased name
- All functionality works correctly in Hebrew and English

### **User Experience Standards**
- Memorial setup can be completed in under 15 minutes
- Mobile-responsive design works on all device sizes
- Hebrew RTL text displays correctly throughout the application
- GPS location capture works reliably on mobile devices
- Video upload and playback functions smoothly

---

## 🔧 Development Notes

### **Hebrew Calendar Integration**
- Use Hebcal API (https://www.hebcal.com/converter) for date conversions
- Yahrzeit calculation: Add 11 months to Hebrew death date
- Handle Hebrew leap years (Adar I/Adar II considerations)
- Store both Hebrew and Gregorian dates for all date fields

### **Photo Processing Requirements**
- Supported formats: JPG, PNG, WebP, GIF
- Maximum file size: 10MB per image
- Generated sizes: thumbnail (400x400), medium (800x600), large (1920x1080)
- Secure filename generation using UUID
- Store in organized directory structure: `/uploads/images/{memorial_id}/`

### **Notification System Architecture**
- Use background job scheduler for automated notifications
- Email templates support both Hebrew (RTL) and English (LTR)
- WhatsApp Business API requires Facebook Business verification
- Store notification delivery status and tracking information
- Support unsubscribe functionality for email notifications

### **Security Considerations**
- Validate all file uploads for malicious content
- Implement rate limiting on API endpoints
- Sanitize all user input, especially Hebrew text
- Use secure filename generation for uploaded files
- Implement proper authentication checks on all protected endpoints

This comprehensive TODO provides the master-python-coder agent with detailed, actionable steps to implement the complete Memorial Website functionality. Each phase builds upon the previous one, ensuring stable, incremental development with proper testing and validation throughout the process.