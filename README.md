# GlobeTrotter Backend API

FastAPI backend for the GlobeTrotter trip planning application with Supabase integration.

## Features

- 🔐 **Authentication**: Supabase Auth integration for user management
- 🗺️ **Trip Management**: Create, update, delete, and list trips
- 🔗 **Public Sharing**: Generate shareable links for trips with read-only access
- 👤 **User Profiles**: Manage user settings, language preferences, and account deletion
- 🛡️ **Row Level Security**: Database-level security with Supabase RLS
- 📱 **RESTful API**: Clean, well-documented API endpoints

## Setup Instructions

### 1. Prerequisites

- Python 3.8+
- Supabase account ([sign up here](https://supabase.com))
- Git

### 2. Supabase Setup

1. Create a new project in Supabase
2. Go to **SQL Editor** in your Supabase dashboard
3. Copy and paste the contents of `supabase_setup.sql`
4. Run the SQL script to create all tables and policies

### 3. Get Supabase Credentials

From your Supabase project dashboard:
1. Go to **Settings** > **API**
2. Copy your **Project URL** (SUPABASE_URL)
3. Copy your **anon public** key (SUPABASE_KEY)
4. Copy your **service_role** key (SUPABASE_SERVICE_KEY) - keep this secure!

### 4. Local Development Setup

```bash
# Clone the repository
git clone <your-repo-url>
cd GlobeTrotterBE

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirement.txt

# Create .env file from example
copy .env.example .env  # Windows
# or
cp .env.example .env    # macOS/Linux
```

### 5. Configure Environment Variables

Edit `.env` file with your Supabase credentials:

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-role-key

SECRET_KEY=generate-a-random-secret-key
```

To generate a secure SECRET_KEY:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 6. Run the Application

```bash
# Development mode with auto-reload
python app/main.py

# Or using uvicorn directly
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at: `http://localhost:8000`

### 7. API Documentation

Once running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## API Endpoints

### Authentication
- `POST /api/v1/auth/signup` - Register new user
- `POST /api/v1/auth/login` - Login user
- `POST /api/v1/auth/logout` - Logout user
- `POST /api/v1/auth/refresh` - Refresh access token

### User Profile
- `GET /api/v1/profile/me` - Get current user profile
- `PUT /api/v1/profile/me` - Update profile
- `DELETE /api/v1/profile/me` - Delete account

### Trips
- `POST /api/v1/trips` - Create new trip
- `GET /api/v1/trips` - List all user trips
- `GET /api/v1/trips/{trip_id}` - Get specific trip
- `PUT /api/v1/trips/{trip_id}` - Update trip
- `DELETE /api/v1/trips/{trip_id}` - Delete trip
- `POST /api/v1/trips/{trip_id}/share` - Generate share link
- `DELETE /api/v1/trips/{trip_id}/share` - Remove sharing
- `GET /api/v1/trips/shared/{share_token}` - View shared trip (public)

## Database Schema

### Tables
- **users**: User profiles (extends Supabase Auth)
- **trips**: Trip information
- **stops**: Trip destinations/stops
- **activities**: Activities at each stop

### Security
All tables use Supabase Row Level Security (RLS) to ensure:
- Users can only access their own data
- Public trips are accessible via share token
- Cascading deletes maintain data integrity

## Project Structure

```
GlobeTrotterBE/
├── app/
│   ├── core/
│   │   ├── config.py          # Application settings
│   │   ├── database.py        # Supabase client
│   │   └── security.py        # Authentication logic
│   ├── models/                # Data models
│   │   ├── user.py
│   │   ├── trip.py
│   │   ├── stop.py
│   │   └── activity.py
│   ├── routes/                # API endpoints
│   │   ├── auth.py
│   │   ├── trips.py
│   │   ├── profile.py
│   │   ├── budget.py
│   │   └── search.py
│   ├── schemas/               # Request/response schemas
│   │   ├── user.py
│   │   ├── trip.py
│   │   └── activity.py
│   └── main.py               # FastAPI application
├── .env.example              # Environment variables template
├── requirement.txt           # Python dependencies
└── supabase_setup.sql       # Database schema
```

## Development

### Testing the API

Example signup request:
```bash
curl -X POST http://localhost:8000/api/v1/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepassword",
    "full_name": "John Doe"
  }'
```

Example create trip request (requires authentication):
```bash
curl -X POST http://localhost:8000/api/v1/trips \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "name": "Paris Adventure",
    "start_date": "2026-06-01",
    "end_date": "2026-06-10",
    "description": "Summer trip to Paris"
  }'
```

## Next Steps

1. **Implement Stop and Activity endpoints**: Add CRUD operations for stops and activities
2. **Budget tracking**: Implement budget calculation features
3. **Foursquare integration**: Add place search functionality
4. **File uploads**: Implement photo upload for trips and activities
5. **Email notifications**: Add email verification and notifications
6. **Rate limiting**: Add API rate limiting for production
7. **Caching**: Implement Redis caching for better performance

## Production Deployment

Before deploying to production:
1. Set `DEBUG=False` in environment variables
2. Use a strong `SECRET_KEY`
3. Configure proper CORS origins
4. Set up SSL/TLS certificates
5. Use environment-specific Supabase projects
6. Enable logging and monitoring
7. Set up backup strategies

## License

MIT License

## Support

For issues and questions, please open an issue on GitHub.
