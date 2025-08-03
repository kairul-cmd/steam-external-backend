# Steam External Backend API

A FastAPI backend application connected to Turso database for Steam-related data management.

## 🚀 Features

- **FastAPI Framework**: High-performance, modern Python web framework
- **Turso Database**: Edge database with global replication
- **Automatic API Documentation**: Interactive Swagger UI and ReDoc
- **Type Safety**: Full type hints with Pydantic models
- **CORS Support**: Cross-origin resource sharing enabled
- **Health Checks**: Built-in health monitoring endpoints
- **Production Ready**: Configured for deployment on Render.com

## 📋 Prerequisites

- Python 3.11+
- Turso database account and database setup
- Git

## 🛠️ Local Development Setup

### 1. Clone the repository
```bash
git clone <your-repo-url>
cd steam-external-backend
```

### 2. Create virtual environment
```bash
python -m venv venv

# On Windows
venv\Scripts\activate

# On macOS/Linux
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Environment Configuration

Copy `.env.example` to `.env` and update with your Turso credentials:

```bash
cp .env.example .env
```

Edit `.env` file:
```env
TURSO_DATABASE_URL=https://your-database-url.turso.io
TURSO_AUTH_TOKEN=your_actual_turso_token
```

### 5. Run the application
```bash
python main.py
```

Or using uvicorn directly:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## 📚 API Documentation

Once the server is running, visit:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## 🔗 API Endpoints

### Health & Status
- `GET /` - Root endpoint
- `GET /health` - Health check with database connectivity test

### User Management
- `POST /users` - Create a new user
- `GET /users` - Get all users
- `GET /users/{user_id}` - Get user by ID
- `DELETE /users/{user_id}` - Delete user by ID

### Example API Usage

#### Create a User
```bash
curl -X POST "http://localhost:8000/users" \
     -H "Content-Type: application/json" \
     -d '{
       "username": "gamer123",
       "email": "gamer123@example.com",
       "steam_id": "76561198000000000"
     }'
```

#### Get All Users
```bash
curl -X GET "http://localhost:8000/users"
```

## 🚀 Deployment on Render.com

### 1. Prepare for deployment

Create `render.yaml` (optional, for infrastructure as code):
```yaml
services:
  - type: web
    name: steam-external-backend
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: TURSO_DATABASE_URL
        value: your_database_url
      - key: TURSO_AUTH_TOKEN
        value: your_auth_token
```

### 2. Deploy to Render

1. **Connect Repository**: Link your GitHub repository to Render
2. **Configure Service**:
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
3. **Set Environment Variables**:
   - `TURSO_DATABASE_URL`: Your Turso database URL
   - `TURSO_AUTH_TOKEN`: Your Turso authentication token
4. **Deploy**: Click deploy and wait for the build to complete

### 3. Verify Deployment

Once deployed, test your API:
- Health check: `https://your-app.onrender.com/health`
- API docs: `https://your-app.onrender.com/docs`

## 🗄️ Database Schema

### Users Table
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    steam_id TEXT UNIQUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

## 🔧 Configuration

The application uses environment variables for configuration. See `config.py` for all available settings.

### Key Environment Variables
- `TURSO_DATABASE_URL`: Your Turso database URL
- `TURSO_AUTH_TOKEN`: Your Turso authentication token
- `HOST`: Server host (default: 0.0.0.0)
- `PORT`: Server port (default: 8000)
- `DEBUG`: Debug mode (default: False)

## 📁 Project Structure

```
steam-external-backend/
├── main.py              # FastAPI application entry point
├── database.py          # Database connection and operations
├── models.py            # Pydantic models for request/response
├── config.py            # Application configuration
├── requirements.txt     # Python dependencies
├── .env.example         # Environment variables template
├── .env                 # Environment variables (not in git)
└── README.md           # This file
```

## 🧪 Testing

### Manual Testing
Use the interactive API documentation at `/docs` to test endpoints.

### Health Check
```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "success": true,
  "message": "API and database are healthy",
  "data": {"status": "healthy"}
}
```

## 🔒 Security Considerations

- **Environment Variables**: Never commit `.env` file to version control
- **CORS**: Configure `cors_origins` properly for production
- **Authentication**: Add authentication middleware for production use
- **Rate Limiting**: Consider adding rate limiting for production
- **Input Validation**: All inputs are validated using Pydantic models

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🆘 Troubleshooting

### Common Issues

1. **Database Connection Failed**
   - Verify `TURSO_DATABASE_URL` and `TURSO_AUTH_TOKEN` are correct
   - Check if your Turso database is active

2. **Import Errors**
   - Ensure all dependencies are installed: `pip install -r requirements.txt`
   - Verify you're using Python 3.11+

3. **Port Already in Use**
   - Change the port in `config.py` or use: `uvicorn main:app --port 8001`

### Getting Help

- Check the API documentation at `/docs`
- Review the logs for detailed error messages
- Ensure all environment variables are properly set