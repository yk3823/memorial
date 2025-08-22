# Memorial Website - Complete Functional Requirements & Implementation Steps

This document outlines the complete functional requirements and remaining development tasks for the Memorial Website project.

## 🎯 Complete User Flow & Functionality Requirements

### **End-to-End User Journey**

1. **User Registration** → User creates account and logs in
2. **Memorial Setup Page** → Comprehensive memorial creation with all media and details  
3. **Memorial Page Creation** → Public memorial page accessible via search
4. **Automated Notifications** → Email and WhatsApp reminders before yahrzeit
5. **Community Features** → WhatsApp group creation for family coordination

### **Memorial Setup Page - Complete Feature Set**

After registration, users are directed to a comprehensive setup page with the following capabilities:

#### **📸 Photo Management (6 Photos Total)**
- **Primary Photo**: Main photo of the deceased (REQUIRED)
- **Grave Photo**: Optional photo of the grave/headstone  
- **Additional Photos**: Up to 4 optional memorial photos
- **Features**: Upload validation, automatic resizing, thumbnail generation, secure storage

#### **📍 Location Management**
- **GPS Location**: Exact coordinates of the grave location (with map interface)
- **Address Input**: Cemetery name and complete grave address
- **Location Services**: Open location in maps (Google, Apple, Waze)
- **Directions Integration**: One-click navigation assistance

#### **📝 Personal Information**
- **Hebrew Name**: REQUIRED - Name of deceased in Hebrew characters
- **English Name**: OPTIONAL - Name in English/Latin characters
- **Text Blocks**: 3 customizable text sections for biography, memories, tributes
- **Date Management**: Death date with automatic Hebrew calendar conversion

#### **🎥 Video Upload**
- **Grave Directions Video**: Optional recording showing pathway to the grave
- **Video Processing**: Automatic compression and optimization for web delivery
- **Secure Storage**: Protected video hosting with streaming capabilities

#### **📧 Email Notification System**
- **Email Contacts**: Up to 5 email addresses for yahrzeit notifications
- **Yahrzeit Calculation**: Automatic Hebrew calendar calculation (11 months after death date)
- **Email Reminders**: Automated reminder emails sent 2 weeks before yahrzeit date
- **Database Integration**: All notification preferences and schedules stored in database

#### **📱 WhatsApp Group Creation**
- **Group Setup**: One-click WhatsApp group creation functionality
- **Member Addition**: Add up to 5 people to the memorial WhatsApp group
- **Custom Message**: Automated welcome message with memorial website link
- **Yahrzeit Notifications**: WhatsApp group reminders sent 2 weeks before memorial date
- **Group Management**: Admin controls for group settings

### **Database Storage Requirements**
All submitted information must be securely stored in PostgreSQL database including:
- All photos with metadata (upload date, file size, dimensions)
- Location data (GPS coordinates, address, cemetery details)
- Personal information (Hebrew/English names, dates, text blocks)
- Video files with processing status and metadata
- Email notification lists with delivery preferences
- WhatsApp group information and member details
- Yahrzeit calculation results and notification schedules

### **Public Memorial Page Creation**
After setup completion, system automatically creates a public memorial page featuring:
- **Search Integration**: Memorial findable by deceased's name on main website
- **Photo Gallery**: Beautiful responsive display of all uploaded photos
- **Memorial Information**: Hebrew/English names, biography, important dates
- **Location Access**: Interactive map with directions to grave site
- **Video Player**: Embedded grave directions video (if uploaded)
- **Contact Information**: Family contact details (privacy-controlled)
- **Yahrzeit Display**: Next memorial date with Hebrew calendar information

### **Automated Systems Integration**

#### **Hebrew Calendar Engine**
- **Date Conversion**: Precise Gregorian to Hebrew calendar conversion
- **Yahrzeit Calculation**: Accurate 11-month Hebrew calendar calculation
- **Leap Year Support**: Handles all Hebrew calendar variations and adjustments
- **Multi-Format Display**: Shows dates in both Hebrew and Gregorian formats

#### **Notification Engine**
- **Email Service**: Automated SMTP-based email delivery system
- **WhatsApp Integration**: Business API integration for group messaging
- **Background Scheduling**: Automated task scheduling for reminder delivery
- **Delivery Tracking**: Comprehensive logging and confirmation system

#### **Search & Discovery**
- **Site-Wide Search**: Memorial pages indexed for name-based searching
- **SEO Optimization**: Public pages optimized for search engine discovery
- **Privacy Controls**: Granular visibility settings for memorial content

## 🔄 **IN PROGRESS**

### Photo Upload Functionality

- **Status**: Ready to implement
- **Description**: Secure photo upload with validation, processing, and storage
- **Features Needed**:
  - File upload validation (size, type, dimensions)
  - Image processing and optimization
  - Secure storage with CDN integration
  - Photo management (up to 4 photos per memorial)
  - Image thumbnail generation
  - Photo ordering and primary photo selection

## 📋 **REMAINING STEPS**

### 1. **Psalm 119 Verse Generation Based on Hebrew Names**

- **Priority**: High
- **Description**: Generate personalized Psalm 119 verses based on Hebrew names
- **Requirements**:
  - Hebrew name letter mapping to Psalm 119 sections
  - Verse selection algorithm based on name letters
  - Support for נשמה (Neshama/Soul) verses
  - Database of all 176 Psalm 119 verses in Hebrew and English
  - Verse display formatting and presentation

### 2. **Email Notification System**

- **Priority**: High
- **Description**: Automated email notifications for yahrzeit reminders and updates
- **Requirements**:
  - Yahrzeit reminder emails (2 weeks before)
  - Memorial update notifications
  - Email template system with Hebrew/English support
  - Bulk email processing
  - Email delivery tracking and bounce handling
  - Unsubscribe management

### 3. **WhatsApp Group Creation Functionality**

- **Priority**: Medium
- **Description**: Create WhatsApp groups for memorial families
- **Requirements**:
  - WhatsApp Business API integration
  - Group creation with up to 5 members
  - Custom group naming (deceased person's name)
  - Invitation link generation
  - Group management and administration
  - Error handling for invalid phone numbers

### 4. **Frontend Templates with Jinja2, Bootstrap, and JavaScript**

- **Priority**: High
- **Description**: Complete web interface for all functionality
- **Requirements**:
  - Responsive design with Bootstrap 5
  - Hebrew/English RTL/LTR support
  - User authentication pages (login, register, verify)
  - Memorial creation and editing forms
  - Memorial display pages (public and private)
  - Dashboard for managing memorials
  - Photo upload and management interface
  - Admin panel for system management

### 5. **Grave Location Management with GPS Option**

- **Priority**: Medium
- **Description**: Cemetery and grave location tracking with GPS integration
- **Requirements**:
  - Cemetery database and location storage
  - GPS coordinate capture and storage
  - Google Maps/Apple Maps integration
  - Directions generation (Google, Apple, Waze)
  - Location verification system
  - Cemetery section, row, plot management
  - Location search and filtering

### 6. **Video Upload for Grave Directions**

- **Priority**: Low
- **Description**: Video recording and upload for grave location guidance
- **Requirements**:
  - Video file upload with validation
  - Video processing and compression
  - Secure video storage and streaming
  - Video player integration
  - Mobile video recording support
  - Video thumbnail generation

### 7. **Memorial Page Display with All Features**

- **Priority**: High
- **Description**: Complete memorial page with all integrated features
- **Requirements**:
  - Beautiful memorial page layout
  - Photo gallery with lightbox
  - Psalm verses display
  - Biography and details section
  - Yahrzeit information display
  - Contact information (if public)
  - Social sharing capabilities
  - Memorial song/audio player
  - Location and directions
  - Visitor comments (optional)

### 8. **Comprehensive Testing Suite**

- **Priority**: High
- **Description**: Full test coverage for all application components
- **Requirements**:
  - Unit tests for all services and utilities
  - Integration tests for API endpoints
  - Database tests with fixtures
  - Authentication and authorization tests
  - Hebrew calendar integration tests
  - Email and notification tests
  - Photo upload and processing tests
  - End-to-end testing with Playwright/Selenium
  - Performance and load testing
  - Security testing

## 🔧 **TECHNICAL DEBT & IMPROVEMENTS**

### Database Migrations

- **Issue**: Database migration needs to be completed successfully
- **Action**: Fix any remaining migration issues and ensure all tables are created

### Performance Optimization

- **Caching**: Implement Redis caching for frequently accessed data
- **Database**: Optimize queries and add proper indexing
- **API**: Add response compression and caching headers

### Security Enhancements

- **Input Validation**: Enhance input sanitization
- **Rate Limiting**: Fine-tune rate limiting rules
- **Security Headers**: Additional security headers implementation
- **Audit Logging**: Comprehensive audit trail

### Monitoring & Observability

- **Logging**: Structured logging with correlation IDs
- **Metrics**: Application metrics and health checks
- **Alerting**: Error monitoring and alerting system
- **Performance**: APM integration

## 📅 **ESTIMATED TIMELINE**

| Task                 | Priority | Estimated Time | Dependencies           |
| -------------------- | -------- | -------------- | ---------------------- |
| Photo Upload         | High     | 2-3 days       | File storage setup     |
| Psalm 119 Generation | High     | 2 days         | Database seeding       |
| Email Notifications  | High     | 2-3 days       | Email service config   |
| Frontend Templates   | High     | 5-7 days       | All backend APIs       |
| Testing Suite        | High     | 3-4 days       | All features complete  |
| WhatsApp Integration | Medium   | 3-4 days       | WhatsApp API access    |
| GPS/Location         | Medium   | 2-3 days       | Maps API setup         |
| Video Upload         | Low      | 2-3 days       | Video processing setup |

**Total Estimated Time**: 20-30 development days

## 🎯 **MVP SCOPE**

For a Minimum Viable Product (MVP) launch, focus on:

### Phase 1 (Essential)

1. ✅ User Authentication
2. ✅ Memorial CRUD Operations
3. ✅ Hebrew Calendar Integration
4. 🔄 Photo Upload (4 photos max)
5. 📋 Psalm 119 Verse Generation
6. 📋 Email Notifications
7. 📋 Frontend Templates

### Phase 2 (Enhanced)

8. 📋 Testing Suite
9. 📋 Memorial Page Display
10. 📋 GPS Location Management

### Phase 3 (Advanced)

11. 📋 WhatsApp Integration
12. 📋 Video Upload

## 🚀 **DEPLOYMENT CONSIDERATIONS**

### Production Environment

- **Hosting**: Cloud platform (AWS, Google Cloud, Azure)
- **Database**: Managed PostgreSQL service
- **Storage**: Object storage for photos/videos (S3, CloudFlare R2)
- **CDN**: Content delivery network for static assets
- **SSL**: HTTPS certificates and security
- **Monitoring**: Application and infrastructure monitoring

### Performance Requirements

- **Response Time**: < 200ms for API endpoints
- **Uptime**: 99.9% availability
- **Scalability**: Handle 1000+ concurrent users
- **Storage**: Support for thousands of photos/videos

## 📝 **NOTES**

- All Hebrew text must be properly encoded (UTF-8)
- Consider cultural sensitivity in all features
- Ensure GDPR compliance for user data
- Plan for multi-language support (Hebrew/English)
- Consider mobile-first responsive design
- Plan for accessibility (WCAG 2.1 compliance)

most importnet , create basic templates html page to make the test easier , please remember taht in order to make it generic we should use the base_template concept of jinja2 , in that way with simple basic html pages we could always
test the flow in a very easy way
