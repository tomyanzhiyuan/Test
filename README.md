# Code Execution Website

A secure, full-stack web application for executing Python code in isolated Docker containers. Built with React (Vite) + TypeScript + Tailwind CSS frontend and FastAPI + Python backend.

## 🚀 Features

- **Secure Code Execution**: Python code runs in AWS Lambda with comprehensive security validation
- **Modern UI**: Clean, responsive interface with Monaco Editor for syntax highlighting
- **Real-time Feedback**: Instant code execution results with error handling
- **Database Persistence**: Successful code submissions are saved to PostgreSQL
- **Pre-installed Libraries**: pandas, scipy, and numpy available out of the box
- **Rate Limiting**: API protection against abuse
- **Type Safety**: Full TypeScript support throughout the stack

## 🏗️ Architecture

### Frontend (React + Vite + TypeScript)
- **Framework**: React 18 with Vite for fast development
- **Styling**: Tailwind CSS for responsive design
- **Code Editor**: Monaco Editor with Python syntax highlighting
- **State Management**: React hooks for local state
- **API Client**: Axios with interceptors for error handling

### Backend (FastAPI + Python 3.12)
- **Framework**: FastAPI with async/await support
- **Database**: PostgreSQL with SQLAlchemy 2.0 ORM
- **Security**: Docker containerization for code execution
- **Validation**: Pydantic models for request/response validation
- **Rate Limiting**: slowapi for API protection

### Security Features
- **AWS Lambda Isolation**: Code execution in secure, isolated AWS Lambda environment
- **Comprehensive Code Validation**: AST parsing and security analysis before execution
- **Resource Limits**: 30-second timeout, memory limits enforced by Lambda
- **Network Isolation**: Lambda provides secure sandboxed execution
- **Input Validation**: Code length limits, complexity analysis, and sanitization
- **Module Restrictions**: Only whitelisted libraries (pandas, scipy, numpy) allowed

## 📋 Prerequisites

- **Docker & Docker Compose**: For containerized deployment
- **Python 3.12+**: For local backend development
- **Node.js 18+**: For local frontend development
- **PostgreSQL 16+**: Database (can run via Docker)

## 🚀 Quick Start

### Using Docker Compose (Recommended)

1. **Clone the repository**
   ```bash
   git clone git@github.com:tomyanzhiyuan/Test.git
   cd code-execution-website
   ```

2. **Set up AWS Lambda credentials**
   ```bash
   # Copy the example file and add your AWS credentials
   cp docker/.env.example docker/.env
   # Edit docker/.env with your AWS credentials:
   # AWS_ACCESS_KEY_ID=your-access-key-id
   # AWS_SECRET_ACCESS_KEY=your-secret-access-key
   ```

3. **Build and start all services**
   ```bash
   cd docker
   docker-compose up --build
   ```

4. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

### Local Development Setup

#### Backend Setup

1. **Navigate to backend directory**
   ```bash
   cd backend
   ```

2. **Install Poetry (if not installed)**
   ```bash
   curl -sSL https://install.python-poetry.org | python3 -
   ```

3. **Install dependencies**
   ```bash
   poetry install
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your database credentials
   ```
   
   **Note**: The .env files have been created from the templates. You can modify them as needed for your environment.

5. **Start PostgreSQL** (using Docker)
   ```bash
   docker run -d \
     --name postgres-dev \
     -e POSTGRES_USER=postgres \
     -e POSTGRES_PASSWORD=password \
     -e POSTGRES_DB=code_execution \
     -p 5432:5432 \
     postgres:16
   ```

6. **Run the backend**
   ```bash
   poetry run uvicorn app.main:app --reload
   ```

#### Frontend Setup

1. **Navigate to frontend directory**
   ```bash
   cd frontend
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your API URL
   ```

4. **Start the development server**
   ```bash
   npm run dev
   ```

## 🔧 Configuration

### Environment Variables

#### Backend (.env)
```env
# Database
POSTGRES_SERVER=localhost
POSTGRES_USER=postgres
POSTGRES_PASSWORD=password
POSTGRES_DB=code_execution
POSTGRES_PORT=5432

# Security
SECRET_KEY=your-secret-key-change-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Code Execution
DOCKER_IMAGE=python:3.12-slim
EXECUTION_TIMEOUT=30
MEMORY_LIMIT=512m
MAX_CODE_LENGTH=10000
RATE_LIMIT=10/minute

# Environment
ENVIRONMENT=development
DEBUG=true
```

#### Frontend (.env)
```env
VITE_API_URL=http://localhost:8000
```

## 📚 API Documentation

The API documentation is automatically generated and available at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Key Endpoints

- `POST /api/v1/code/execute` - Execute code without saving
- `POST /api/v1/code/submit` - Execute and save code to database
- `GET /api/v1/code/submissions/{id}` - Retrieve saved submission

## 🧪 Testing

### Backend Tests
```bash
cd backend
poetry run pytest
```

### Frontend Tests
```bash
cd frontend
npm run test
```

## 🔒 Security Framework

### **Multi-Layer Security Architecture**

#### **1. Code Validation & Analysis**
- **AST Analysis**: Parse and analyze Python code structure
- **Module Blacklisting**: Block dangerous imports (os, sys, subprocess, socket, etc.)
- **Function Restrictions**: Prevent use of eval(), exec(), open(), input()
- **Complexity Limits**: Restrict code complexity to prevent resource exhaustion
- **Pattern Detection**: Regex-based detection of malicious patterns

#### **2. Container Isolation**
- **Secure Execution Image**: Hardened container with minimal attack surface
- **Non-root User**: Code runs as unprivileged 'coderunner' user
- **Read-only Filesystem**: Prevents file system modifications
- **Network Isolation**: No external network access
- **Capability Dropping**: Remove all Linux capabilities
- **Resource Limits**: 512MB RAM, 50% CPU quota, 30-second timeout

#### **3. Input Validation**
- **Code Length**: Maximum 10KB per submission
- **Line Limits**: Maximum 100 lines of code
- **Syntax Validation**: Ensure valid Python syntax
- **Import Restrictions**: Only allow whitelisted modules
- **Rate Limiting**: 10 requests per minute per IP

#### **4. Error Handling & Information Disclosure Prevention**
- **Error Sanitization**: Remove file paths and system information
- **Message Truncation**: Limit error message length
- **Container ID Masking**: Hide Docker container identifiers
- **Path Obfuscation**: Replace system paths with generic placeholders

#### **5. Allowed Operations**
**Safe Modules Only:**
- **Data Science**: pandas, numpy, scipy
- **Standard Library**: math, statistics, random, datetime, json, csv
- **Utilities**: re, collections, itertools, functools, operator

**Blocked Operations:**
- File system access (open, file operations)
- Network operations (socket, urllib, requests)
- System calls (os, sys, subprocess)
- Code execution (eval, exec, compile)
- Import manipulation (__import__, importlib)
- Serialization (pickle, marshal)
- Multi-processing/threading

## 🚀 Deployment

### Production Deployment

1. **Update environment variables** for production
2. **Build Docker images**
   ```bash
   docker-compose -f docker-compose.prod.yml build
   ```
3. **Deploy with orchestration** (Kubernetes, Docker Swarm, etc.)

### Security Hardening for Production

- Change default passwords and secrets
- Enable HTTPS with SSL certificates
- Set up proper firewall rules
- Configure log monitoring and alerting
- Regular security updates for base images

## 🛠️ Development

### Code Style

- **Python**: Black formatter, isort for imports, mypy for type checking
- **TypeScript**: Prettier formatter, ESLint for linting
- **Commits**: Conventional commit format

### Project Structure

```
code-execution-website/
├── .clinerules                 # Cline development rules
├── backend/                    # FastAPI backend
│   ├── app/
│   │   ├── api/               # API routes
│   │   ├── core/              # Core configuration
│   │   ├── db/                # Database setup
│   │   ├── models/            # SQLAlchemy models
│   │   ├── schemas/           # Pydantic schemas
│   │   └── services/          # Business logic
│   ├── tests/                 # Backend tests
│   ├── Dockerfile
│   └── pyproject.toml
├── frontend/                   # React frontend
│   ├── src/
│   │   ├── components/        # React components
│   │   ├── services/          # API services
│   │   ├── types/             # TypeScript types
│   │   └── App.tsx
│   ├── Dockerfile
│   └── package.json
└── docker/                    # Docker configuration
    ├── docker-compose.yml
    └── Dockerfile.execution
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes following the code style guidelines
4. Add tests for new functionality
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Troubleshooting

### Common Issues

1. **Docker permission errors**
   ```bash
   sudo usermod -aG docker $USER
   # Log out and back in
   ```

2. **Port already in use**
   ```bash
   # Check what's using the port
   lsof -i :8000
   # Kill the process or change the port
   ```

3. **Database connection errors**
   - Ensure PostgreSQL is running
   - Check connection credentials
   - Verify network connectivity

### Getting Help

- Check the [Issues](https://github.com/your-repo/issues) page
- Review API documentation at `/docs`
- Check Docker logs: `docker-compose logs`

## 🔮 Future Enhancements

- [ ] Support for additional programming languages
- [ ] User authentication and authorization
- [ ] Code sharing and collaboration features
- [ ] Advanced code analysis and metrics
- [ ] Integration with external APIs
- [ ] Real-time collaborative editing
