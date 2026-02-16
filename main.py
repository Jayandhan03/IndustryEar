from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from src.agent import agent  

app = FastAPI()

# ---------- CORS (VERY IMPORTANT for Next.js) ----------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.js frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- Request Schema ----------
class NewsRequest(BaseModel):
    topic: str


# ---------- Health Check ----------
@app.get("/")
def read_root():
    return {"status": "FastAPI backend running"}


# ---------- Generate News Endpoint ----------
@app.post("/generate-news")
async def generate_news(data: NewsRequest):
    try:
        # Pass topic into your agent if needed
        result = agent()  
        # If your agent does NOT accept topic, use: result = agent()

        return {
            "success": True,
            "news": result
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
