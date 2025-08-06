# AI Agents MCP Client

A FastAPI-based client application that leverages the Model Context Protocol (MCP) to provide AI-powered services for e-commerce operations, including product management, recommendations, and order processing.

## 🚀 Overview

The AI Agents MCP Client is a sophisticated microservice that connects to MCP servers to provide intelligent automation for e-commerce workflows. It offers RESTful APIs for product categorization, performance analytics, personalized recommendations, and automated order processing using AI agents.

## ✨ Key Features

### 🛍️ Product Management
- **Product Categorization**: Automatically categorize products using AI
- **Performance Analytics**: Track and analyze product performance metrics
- **Product Data Processing**: Handle product information with intelligent preprocessing

### 🎯 Recommendations System
- **Vector-Based Search**: Powered by Pinecone for semantic product matching
- **User Profile Building**: Create comprehensive user profiles for personalization
- **Document Chunking**: Process and chunk product descriptions for better search
- **Embedding Generation**: Generate embeddings for similarity matching

### 📦 Order Processing
- **AI-Powered Automation**: Intelligent order processing using MCP tools
- **Context Acquisition**: Automatically gather customer and product context
- **Approval Workflows**: Handle order approvals and adjustments
- **Multi-tool Integration**: Leverage multiple MCP tools for comprehensive processing

### 🔧 Technical Capabilities
- **MCP Integration**: Seamless connection to Model Context Protocol servers
- **Vector Database**: Pinecone integration for scalable vector operations
- **Document Processing**: Advanced chunking and preprocessing services
- **Error Handling**: Comprehensive error management with detailed responses
- **Real-time Logging**: Colorized logging for better development experience

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   FastAPI App   │────│  MCP Client      │────│   MCP Server    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │
         │                       │
         ▼                       ▼
┌─────────────────┐    ┌──────────────────┐
│  Vector DB      │    │   OpenAI API     │
│  (Pinecone)     │    │                  │
└─────────────────┘    └──────────────────┘
```

## 📋 Prerequisites

- Python 3.11 or higher
- Poetry for dependency management
- Access to OpenAI API
- Pinecone account (for vector operations)
- MCP Server instance

## 🛠️ Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd ai-agents-mcp-client
   ```

2. **Install dependencies using Poetry**
   ```bash
   poetry install
   ```

3. **Activate the virtual environment**
   ```bash
   poetry shell
   ```

## ⚙️ Environment Configuration

Create a `.env` file in the root directory with the following variables:

### Required Environment Variables

```env
# MCP Configuration
MCP_SERVER_SCRIPT_PATH=/path/to/your/mcp/server/script.py

# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Pinecone Configuration (for vector operations)
PINECONE_API_KEY=your_pinecone_api_key
PINECONE_ENVIRONMENT=your_pinecone_environment
PINECONE_INDEX_NAME=vector_index
PINECONE_HOST=https://your-pinecone-host.com

# Server Configuration
PORT=8000
```

### Environment Variable Details

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `MCP_SERVER_SCRIPT_PATH` | Path to the MCP server script | ✅ Yes | - |
| `OPENAI_API_KEY` | OpenAI API key for AI services | ✅ Yes | - |
| `PINECONE_API_KEY` | Pinecone API key for vector operations | ✅ Yes | - |
| `PINECONE_ENVIRONMENT` | Pinecone environment | ✅ Yes | - |
| `PINECONE_INDEX_NAME` | Name of the Pinecone index | ❌ No | `vector_index` |
| `PINECONE_HOST` | Pinecone host URL | ❌ No | `http://localhost:5080` |
| `PORT` | Server port | ❌ No | `8000` |

## 🚀 How to Run

### Development Mode

```bash
# Using Poetry
poetry run python src/ai-agents-mcp-client/main.py

# Or if virtual environment is activated
python src/ai-agents-mcp-client/main.py
```

### Production Mode

```bash
# Using uvicorn directly
uvicorn main:app --host 0.0.0.0 --port 8000

# Or with custom configuration
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Using Docker (if Dockerfile exists)

```bash
docker build -t ai-agents-mcp-client .
docker run -p 8000:8000 --env-file .env ai-agents-mcp-client
```

## 📚 API Documentation

Once the server is running, you can access:

- **API Documentation**: `http://localhost:8000/docs` (Swagger UI)
- **Health Check**: `http://localhost:8000/health-check`

### Available Endpoints

#### Product Management
- `POST /categorize` - Categorize products using AI
- `GET /products/performance` - Get product performance analytics

#### Recommendations
- `POST /recommendations/embeddings` - Generate product embeddings
- `POST /recommendations/relevant-products` - Get relevant product recommendations
- `POST /recommendations/user-profile` - Build user profiles

#### Order Processing
- `POST /order-processing/process` - Process orders with AI agents
- `POST /order-processing/approval` - Handle order approvals

## 🧩 Core Components

### MCP Client Manager
Manages connections to MCP servers and provides a singleton interface for MCP operations.

### Vector Database
Handles vector storage and similarity search using Pinecone for semantic matching.

### Services
- **ProductService**: Product categorization and management
- **RecommendationsService**: Recommendation generation and user profiling
- **OrderProcessingService**: AI-powered order processing
- **ChunkingService**: Document chunking and preprocessing
- **PreprocessService**: Data preprocessing and embedding generation

## 🔧 Development

### Project Structure

```
src/ai-agents-mcp-client/
├── main.py                      # FastAPI application entry point
├── mcp_client.py               # MCP client implementation
├── core/                       # Core components
│   ├── client_manager.py       # MCP client management
│   └── vector_db.py           # Vector database operations
├── products/                   # Product management
├── recommendations/            # Recommendation system
├── order_processing/          # Order processing
├── chunking/                  # Document chunking
├── preprocess/               # Data preprocessing
├── exceptions/               # Custom exceptions
└── schemas/                  # Data schemas
```

### Adding New Features

1. Create new service in appropriate module directory
2. Define DTOs for request/response models
3. Implement controller with FastAPI router
4. Add router to main application
5. Update tests and documentation

## 🐛 Troubleshooting

### Common Issues

1. **MCP Connection Failed**
   - Verify `MCP_SERVER_SCRIPT_PATH` is correct
   - Ensure MCP server is accessible
   - Check server logs for connection errors

2. **Vector Database Errors**
   - Verify Pinecone credentials
   - Check index exists and is accessible
   - Ensure proper dimensions for embeddings

3. **OpenAI API Errors**
   - Verify API key is valid
   - Check rate limits and quotas
   - Ensure proper model access

### Logging

The application uses structured logging with color coding:
- **INFO**: General information (White)
- **ERROR**: Error messages (Red)  
- **WARNING**: Warnings (Blue)
- **DEBUG**: Debug information (White)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the terms specified in the project configuration.

## 🆘 Support

For support, please:
1. Check the troubleshooting section
2. Review API documentation at `/docs`
3. Check application logs for errors
4. Contact the development team

---

**Note**: Ensure all environment variables are properly configured before running the application. The MCP server must be running and accessible for the client to function correctly.
