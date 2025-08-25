# Memorial Website - Digital Memorial Platform

A comprehensive web application for creating and managing digital memorial pages with Hebrew calendar integration, designed specifically for Jewish families and communities.

## 🌟 Overview

The Memorial Website is a FastAPI-based application that allows families to create beautiful, personalized memorial pages for their deceased loved ones. The platform features Hebrew calendar integration for yahrzeit (memorial anniversary) tracking, email notifications, and community features.

## ✨ Key Features

### 🔐 **Authentication & Security**
- JWT-based authentication with access and refresh tokens
- Email verification for new accounts
- Password reset functionality
- Role-based authorization (User, Admin)
- Rate limiting and security middleware
- CSRF protection

### 📝 **Memorial Management**
- Create personalized memorial pages with Hebrew and English names
- Hebrew calendar integration for yahrzeit calculations
- Public and private memorial pages with unique URLs
- Biography and memorial song support
- Advanced search and filtering
- Memorial statistics and analytics

### 📅 **Hebrew Calendar Integration**
- Automatic Hebrew date conversion using HebCal API
- Yahrzeit calculation (11 months after death in Hebrew calendar)
- Support for Hebrew leap years
- Next yahrzeit date computation

### 👥 **User Management**
- User registration and profile management
- Subscription status tracking (Trial, Active, Expired)
- Memorial ownership validation
- Activity logging

### 🏗️ **Technical Architecture**
- FastAPI with async/await for high performance
- PostgreSQL database with SQLAlchemy ORM
- Redis for caching (via Docker)
- Pydantic for data validation
- Alembic for database migrations
- Comprehensive logging and monitoring

## 🎨 Web Interface & Templates

The application includes a comprehensive web interface built with Jinja2 templates and Bootstrap 5, providing an intuitive way to test and interact with all features.

### **Templates Architecture**

The application uses a modular template structure with Jinja2 inheritance:

```
app/templates/
├── base.html                 # Base template with navigation and layout
├── index.html               # Homepage with feature showcase
├── dashboard.html           # User dashboard with statistics
├── auth/
│   ├── login.html          # Login page with validation
│   └── register.html       # Registration page with form validation
├── memorial/
│   ├── list.html           # Memorial list with search/filter
│   ├── create.html         # Memorial creation form
│   └── public.html         # Public memorial display
└── errors/
    ├── 404.html            # Custom 404 error page
    └── 500.html            # Custom 500 error page
```

### **Key Features**

✅ **Responsive Design** - Mobile-first with Bootstrap 5.3.0  
✅ **Hebrew Support** - RTL text direction and Hebrew fonts (Noto Sans Hebrew)  
✅ **Authentication Integration** - User state-aware navigation  
✅ **API Integration** - JavaScript utilities for seamless API communication  
✅ **Form Validation** - Client-side validation with real-time feedback  
✅ **Loading States** - Button spinners and loading indicators  
✅ **Flash Messages** - Success/error notification system  
✅ **Testing Tools** - Built-in API testing interface on homepage  

### **Accessing the Web Interface**

1. **Start the application:**
```bash
python main.py
```

2. **Navigate to the web interface:**
- Homepage: http://localhost:8000/
- Login: http://localhost:8000/login
- Register: http://localhost:8000/register
- Dashboard: http://localhost:8000/dashboard (requires login)
- Memorials: http://localhost:8000/memorials (requires login)
- Create Memorial: http://localhost:8000/memorials/create (requires login)

### **JavaScript Utilities**

The templates include a global `MemorialApp` JavaScript object with utility functions:

```javascript
// API base URL
MemorialApp.API_BASE = '/api/v1';

// Show flash message
MemorialApp.showFlash('Success!', 'success');

// Button loading states
MemorialApp.showButtonLoading(button);
MemorialApp.hideButtonLoading(button);

// Hebrew text validation
MemorialApp.isHebrewText(text);
```

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Docker and Docker Compose
- PostgreSQL (via Docker)
- Redis (via Docker)

### Installation

1. **Clone and navigate to the project:**
```bash
cd /Users/josephkeinan/memorial
```

2. **Start the database services:**
```bash
docker-compose up -d
```

3. **Set up Python environment:**
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

4. **Install dependencies:**
```bash
pip install -r requirements.txt
```

5. **Configure environment variables:**
```bash
# Edit .env file with your settings
cp .env .env.local
# Update database passwords, JWT secrets, email settings, etc.
```

6. **Initialize the database:**
```bash
# Create tables using the SQL script
docker exec -i memorial_postgres psql -U memorial_user -d memorial_db < create_tables.sql

# Or use Alembic migrations
alembic upgrade head
```

7. **Start the application:**
```bash
# Simple startup (recommended)
python main.py

# Or use uvicorn directly with hot reload
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

8. **Access the application:**
- Web Interface: http://localhost:8000
- API documentation: http://localhost:8000/docs
- Alternative docs: http://localhost:8000/redoc
- Health check: http://localhost:8000/health

## 📖 API Documentation

The application provides comprehensive API documentation via FastAPI's automatic OpenAPI generation:

- **Interactive API Docs**: http://localhost:8000/docs
- **ReDoc Documentation**: http://localhost:8000/redoc
- **OpenAPI Schema**: http://localhost:8000/openapi.json

### Key API Endpoints

#### Authentication
- `POST /api/v1/auth/register` - User registration
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/logout` - User logout
- `GET /api/v1/auth/me` - Get current user
- `POST /api/v1/auth/refresh` - Refresh access token

#### Memorial Management
- `POST /api/v1/memorials` - Create memorial
- `GET /api/v1/memorials` - List user memorials
- `GET /api/v1/memorials/{id}` - Get memorial details
- `PUT /api/v1/memorials/{id}` - Update memorial
- `DELETE /api/v1/memorials/{id}` - Delete memorial
- `GET /api/v1/memorials/{slug}/public` - Public memorial view

## 🧪 Manual Testing

### **Web Interface Testing**

The application includes a user-friendly web interface for easy testing:

1. **Start the Application**
```bash
# Make sure Docker services are running
docker-compose up -d

# Start the FastAPI application (simple method)
python main.py
```

2. **Access the Web Interface**
- Navigate to http://localhost:8000
- Use the built-in API testing tools on the homepage
- Test system health, user authentication, and memorial APIs with one click

3. **Test User Registration & Login**
- Go to http://localhost:8000/register
- Create a new account
- Login at http://localhost:8000/login
- Access your dashboard at http://localhost:8000/dashboard

4. **Test Memorial Features**
- Create memorials at http://localhost:8000/memorials/create
- View your memorials at http://localhost:8000/memorials
- Access public memorial pages

### **API Testing (Command Line)**

### 1. **Start the Application**
```bash
# Make sure Docker services are running
docker-compose up -d

# Activate virtual environment
source venv/bin/activate

# Start the FastAPI application
python main.py
```

### 2. **Test Health Endpoints**
```bash
# Check application health
curl http://localhost:8000/health

# Check API info
curl http://localhost:8000/api/v1/info
```

### 3. **Test User Registration**
```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "SecurePass123!",
    "first_name": "Test",
    "last_name": "User"
  }'
```

### 4. **Test User Login**
```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "SecurePass123!"
  }'
```

### 5. **Test Memorial Creation**
```bash
# First login and get the access token, then:
curl -X POST "http://localhost:8000/api/v1/memorials" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "deceased_name_hebrew": "יוסף בן אברהם",
    "deceased_name_english": "Joseph Ben Abraham",
    "death_date_gregorian": "2023-01-15",
    "biography": "A loving father and devoted husband..."
  }'
```

### 6. **Test Public Memorial Access**
```bash
# Get memorial slug from previous response, then:
curl http://localhost:8000/api/v1/memorials/joseph-ben-abraham-2023/public
```

### **Comprehensive API Test Results**

The application has been thoroughly tested with comprehensive API endpoint testing:

- **Total Tests**: 26 endpoints across 4 categories
- **Success Rate**: 80.8% (21/26 endpoints working)
- **System Health**: 6/6 endpoints working (100%)
- **Authentication**: 13/13 endpoints working (100%)
- **Memorial Operations**: 2/4 endpoints working (50%)
- **Error Handling**: All error responses properly formatted

**Test Reports Available:**
- Detailed test results: `MEMORIAL_API_TEST_REPORT.md`
- Test script: `comprehensive_api_test.py`

Run the comprehensive test suite:
```bash
python comprehensive_api_test.py
```

## 🏗️ Database Management

### View Database Tables
```bash
# Connect to PostgreSQL
docker exec -it memorial_postgres psql -U memorial_user -d memorial_db

# List tables
\dt

# View users
SELECT email, first_name, last_name, is_active FROM users;

# View memorials
SELECT deceased_name_english, owner_id, is_public FROM memorials;
```

### Run Migrations
```bash
# Create new migration
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# View migration history
alembic history
```

## 🐳 Docker Services

The application uses Docker Compose for managing services:

```bash
# Start all services
docker-compose up -d

# View running services
docker-compose ps

# View logs
docker-compose logs -f postgres
docker-compose logs -f redis

# Stop services
docker-compose down
```

### Service URLs
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379
- **pgAdmin** (if enabled): http://localhost:5050

## 🔧 Configuration

Key configuration files:
- `.env` - Environment variables
- `alembic.ini` - Database migration settings
- `docker-compose.yml` - Docker services configuration
- `requirements.txt` - Python dependencies

### Important Environment Variables
```bash
# Database
DATABASE_URL=postgresql+asyncpg://memorial_user:memorial_pass_123@localhost:5432/memorial_db

# Security
SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-here

# Email
EMAIL_HOST=smtp.gmail.com
EMAIL_USERNAME=your-email@gmail.com
EMAIL_PASSWORD=your-app-password
```

## 📊 Monitoring & Logs

### Application Logs
```bash
# View application logs (if using systemd/docker)
tail -f logs/memorial.log

# Or use Python logging in development
# Logs are printed to console in development mode
```

### Database Monitoring
```bash
# Check database connections
docker exec memorial_postgres pg_stat_activity -c "SELECT * FROM pg_stat_activity WHERE datname='memorial_db';"

# View database size
docker exec memorial_postgres psql -U memorial_user -d memorial_db -c "SELECT pg_size_pretty(pg_database_size('memorial_db'));"
```

## 🤝 Contributing

1. Follow the existing code structure and patterns
2. Use async/await for database operations
3. Include proper error handling and validation
4. Add tests for new functionality
5. Update API documentation
6. Follow security best practices

## 📄 License

This project is developed for the Memorial Website platform. All rights reserved.

## 🆘 Troubleshooting

### Common Issues

1. **Database Connection Failed**
   ```bash
   # Ensure PostgreSQL is running
   docker-compose up postgres -d
   
   # Check connection
   docker exec memorial_postgres pg_isready -U memorial_user
   ```

2. **Migration Errors**
   ```bash
   # Reset database (CAUTION: This deletes all data)
   docker exec memorial_postgres psql -U memorial_user -d memorial_db -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
   alembic upgrade head
   ```

3. **Import Errors**
   ```bash
   # Ensure virtual environment is activated
   source venv/bin/activate
   
   # Reinstall dependencies
   pip install -r requirements.txt
   ```

4. **Port Already in Use**
   ```bash
   # Find process using port 8000
   lsof -i :8000
   
   # Kill process if needed
   kill -9 <PID>
   ```

For more help, check the application logs and API documentation at http://localhost:8000/docs