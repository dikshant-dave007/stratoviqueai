"""StratoviqueAI — Entry Point"""
import os
import uvicorn
import dotenv

dotenv.load_dotenv()
# Importing workflow to ensure it's registered before the app starts
if __name__ == "__main__":
    uvicorn.run(
        "backend.main:app",
        host=os.getenv("APP_HOST", "0.0.0.0"),
        port=int(os.getenv("APP_PORT", 8012)),
        reload=os.getenv("APP_ENV") == "development",
        log_level="info",
    )
