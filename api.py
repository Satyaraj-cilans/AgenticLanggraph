from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
from dotenv import load_dotenv
import asyncio
from typing import Optional
import logging
import traceback

# Load environment variables first
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try to import NewsletterGenerator with detailed error handling
NewsletterGenerator = None
import_error = None

try:
    from main import NewsletterGenerator
    logger.info("Successfully imported NewsletterGenerator from main.py")
except ImportError as e:
    import_error = f"ImportError: {str(e)}"
    logger.error(f"Failed to import NewsletterGenerator: {import_error}")
except Exception as e:
    import_error = f"General error: {str(e)}"
    logger.error(f"Failed to import NewsletterGenerator: {import_error}")
    logger.error(f"Full traceback: {traceback.format_exc()}")

# If import failed, create a fallback generator
if NewsletterGenerator is None:
    logger.warning("Creating fallback NewsletterGenerator class")
    
    class FallbackNewsletterGenerator:
        def __init__(self, topic: str, search_limit: int = 5, time_range: str = "qdr:w"):
            self.topic = topic
            self.search_limit = search_limit
            self.time_range = time_range
            
        def generate(self) -> str:
            return f"""# Newsletter: {self.topic}

## System Notice
The AI newsletter generation system is currently experiencing technical difficulties.

## Issue Details
- Import Error: {import_error or 'Unknown import error'}
- This is likely due to missing dependencies or configuration issues

## Troubleshooting Steps
1. Check that all required packages are installed
2. Verify API keys are properly configured
3. Ensure the agno library is compatible with your system
4. Review Docker container logs for detailed error messages

## Technical Information
- Topic requested: {self.topic}
- Articles requested: {self.search_limit}
- Time range: {self.time_range}

Please check the container logs and fix the underlying issue."""
    
    NewsletterGenerator = FallbackNewsletterGenerator

# Create FastAPI app
app = FastAPI(
    title="AI Newsletter Generator API",
    description="Generate newsletters using AI and NewsAPI",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for request/response
class NewsletterRequest(BaseModel):
    topic: str
    search_limit: Optional[int] = 5
    time_range: Optional[str] = "qdr:w"

class NewsletterResponse(BaseModel):
    newsletter: str
    status: str = "success"

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "AI Newsletter Generator API is running!",
        "status": "healthy",
        "endpoints": {
            "generate_newsletter": "/generate_newsletter (POST)",
            "health": "/health (GET)"
        }
    }

@app.get("/health")
async def health_check():
    """Detailed health check"""
    
    # Check if we have the real NewsletterGenerator or fallback
    is_real_generator = True
    try:
        from main import NewsletterGenerator as TestGenerator
        # Try to create an instance to test if it actually works
        test_gen = TestGenerator("test", 1)
        generator_status = True
    except Exception as e:
        is_real_generator = False
        generator_status = False
        logger.error(f"NewsletterGenerator test failed: {str(e)}")
    
    return {
        "status": "healthy",
        "api_keys_configured": {
            "NEBIUS_API_KEY": bool(os.getenv("NEBIUS_API_KEY")),
            "NEWSAPI_API_KEY": bool(os.getenv("NEWSAPI_API_KEY"))
        },
        "newsletter_generator_available": generator_status,
        "using_fallback_generator": not is_real_generator,
        "import_error": import_error if import_error else None
    }

@app.post("/generate_newsletter", response_model=NewsletterResponse)
async def generate_newsletter(request: NewsletterRequest):
    """Generate a newsletter based on the provided topic and parameters"""
    
    logger.info(f"Received request: topic='{request.topic}', search_limit={request.search_limit}, time_range='{request.time_range}'")
    
    # Validate input
    if not request.topic or not request.topic.strip():
        raise HTTPException(status_code=400, detail="Topic is required and cannot be empty")
    
    # Check API keys
    nebius_key = os.getenv("NEBIUS_API_KEY")
    newsapi_key = os.getenv("NEWSAPI_API_KEY")
    
    if not nebius_key:
        raise HTTPException(status_code=500, detail="NEBIUS_API_KEY is not configured")
    if not newsapi_key:
        raise HTTPException(status_code=500, detail="NEWSAPI_API_KEY is not configured")
    
    try:
        logger.info("Creating NewsletterGenerator instance...")
        
        # Create generator instance
        generator = NewsletterGenerator(
            topic=request.topic.strip(),
            search_limit=request.search_limit,
            time_range=request.time_range
        )
        
        logger.info("Generating newsletter...")
        
        # Generate newsletter
        # Run in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        content = await loop.run_in_executor(None, generator.generate)
        
        logger.info("Newsletter generated successfully")
        
        if not content:
            raise HTTPException(status_code=500, detail="Newsletter generation returned empty content")
        
        return NewsletterResponse(newsletter=content, status="success")
        
    except Exception as e:
        error_msg = f"Error generating newsletter: {str(e)}"
        logger.error(error_msg, exc_info=True)
        raise HTTPException(status_code=500, detail=error_msg)

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return {"error": f"Internal server error: {str(exc)}"}

if __name__ == "__main__":
    import uvicorn
    
    # Check environment and imports
    print("="*50)
    print("FASTAPI SERVER STARTUP")
    print("="*50)
    print(f"NEBIUS_API_KEY configured: {bool(os.getenv('NEBIUS_API_KEY'))}")
    print(f"NEWSAPI_API_KEY configured: {bool(os.getenv('NEWSAPI_API_KEY'))}")
    print(f"NewsletterGenerator available: {NewsletterGenerator is not None}")
    print(f"Import error: {import_error}")
    print("="*50)
    
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000,
        log_level="info"
    )