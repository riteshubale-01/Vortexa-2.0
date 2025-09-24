from fastapi import FastAPI, APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime, timezone
import jwt
from passlib.context import CryptContext
import json
try:
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    SENTIMENT_AI_AVAILABLE = True
except ImportError:
    SENTIMENT_AI_AVAILABLE = False
    print("Warning: emergentintegrations not available, using fallback sentiment analysis")

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Authentication setup
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()
JWT_SECRET = os.environ.get('JWT_SECRET', 'your-secret-key-here')

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                # Remove broken connections
                self.active_connections.remove(connection)

manager = ConnectionManager()

# Pydantic Models
class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    username: str
    email: str
    hashed_password: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class UserCreate(BaseModel):
    username: str
    email: str
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    created_at: datetime

class SentimentAnalysis(BaseModel):
    label: str  # Positive, Neutral, Negative
    confidence: float
    explanation: str

class Post(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    body: str
    author_id: str
    author_username: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    sentiment: Optional[SentimentAnalysis] = None

class PostCreate(BaseModel):
    title: str
    body: str

class PostResponse(BaseModel):
    id: str
    title: str
    body: str
    author_username: str
    created_at: datetime
    sentiment: Optional[SentimentAnalysis] = None

# Helper functions
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict) -> str:
    return jwt.encode(data, JWT_SECRET, algorithm="HS256")

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=["HS256"])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Could not validate credentials")
        
        user = await db.users.find_one({"id": user_id})
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")
        return User(**user)
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")

async def analyze_sentiment(text: str) -> SentimentAnalysis:
    """Analyze sentiment using OpenAI GPT-5"""
    if SENTIMENT_AI_AVAILABLE:
        try:
            # Initialize the chat with GPT-5
            chat = LlmChat(
                api_key=os.environ.get('EMERGENT_LLM_KEY'),
                session_id=f"sentiment-{uuid.uuid4()}",
                system_message="You are a sentiment analysis expert. Analyze the given text and respond only with a JSON object containing: sentiment (Positive/Neutral/Negative), confidence (0-1), explanation (one line). Example: {\"sentiment\": \"Positive\", \"confidence\": 0.85, \"explanation\": \"The text expresses happiness and satisfaction.\"}"
            ).with_model("openai", "gpt-5")
            
            # Create the user message
            user_message = UserMessage(text=f"Analyze the sentiment of this text: {text}")
            
            # Send the message and get response
            response = await chat.send_message(user_message)
            
            # Parse the JSON response
            result = json.loads(response)
            
            return SentimentAnalysis(
                label=result["sentiment"],
                confidence=float(result["confidence"]),
                explanation=result["explanation"]
            )
        except Exception as e:
            logging.error(f"AI Sentiment analysis error: {e}")
            # Fallback to rule-based analysis
            return fallback_sentiment_analysis(text)
    else:
        # Use fallback sentiment analysis
        return fallback_sentiment_analysis(text)

def fallback_sentiment_analysis(text: str) -> SentimentAnalysis:
    """Simple rule-based sentiment analysis as fallback"""
    text_lower = text.lower()
    
    positive_words = ['good', 'great', 'awesome', 'amazing', 'excellent', 'wonderful', 'fantastic', 
                     'love', 'like', 'happy', 'joy', 'excited', 'perfect', 'best', 'brilliant',
                     'outstanding', 'superb', 'delighted', 'pleased', 'satisfied', 'grateful']
    
    negative_words = ['bad', 'terrible', 'awful', 'horrible', 'worst', 'hate', 'dislike', 'sad', 
                     'angry', 'frustrated', 'disappointed', 'annoying', 'boring', 'disgusting',
                     'pathetic', 'useless', 'stupid', 'ridiculous', 'failure', 'broken']
    
    positive_count = sum(1 for word in positive_words if word in text_lower)
    negative_count = sum(1 for word in negative_words if word in text_lower)
    
    if positive_count > negative_count:
        confidence = min(0.9, 0.6 + (positive_count - negative_count) * 0.1)
        return SentimentAnalysis(
            label="Positive",
            confidence=confidence,
            explanation="Text contains positive language and expressions"
        )
    elif negative_count > positive_count:
        confidence = min(0.9, 0.6 + (negative_count - positive_count) * 0.1)
        return SentimentAnalysis(
            label="Negative", 
            confidence=confidence,
            explanation="Text contains negative language and expressions"
        )
    else:
        return SentimentAnalysis(
            label="Neutral",
            confidence=0.7,
            explanation="Text appears balanced or neutral in tone"
        )

# Authentication Routes
@api_router.get("/")
async def root():
    return {"message": "SentiFeed API - AI-Powered Sentiment Analysis", "status": "running"}

@api_router.post("/auth/register", response_model=UserResponse)
async def register(user_create: UserCreate):
    # Check if user already exists
    existing_user = await db.users.find_one({"email": user_create.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    existing_username = await db.users.find_one({"username": user_create.username})
    if existing_username:
        raise HTTPException(status_code=400, detail="Username already taken")
    
    # Create new user
    hashed_password = get_password_hash(user_create.password)
    user = User(
        username=user_create.username,
        email=user_create.email,
        hashed_password=hashed_password
    )
    
    await db.users.insert_one(user.dict())
    
    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        created_at=user.created_at
    )

@api_router.post("/auth/login")
async def login(user_login: UserLogin):
    user = await db.users.find_one({"email": user_login.email})
    if not user or not verify_password(user_login.password, user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    
    access_token = create_access_token(data={"sub": user["id"]})
    return {"access_token": access_token, "token_type": "bearer", "user": {
        "id": user["id"],
        "username": user["username"],
        "email": user["email"]
    }}

# Posts Routes
@api_router.post("/posts", response_model=PostResponse)
async def create_post(post_create: PostCreate, current_user: User = Depends(get_current_user)):
    # Analyze sentiment of the post
    combined_text = f"{post_create.title} {post_create.body}"
    sentiment = await analyze_sentiment(combined_text)
    
    # Create post
    post = Post(
        title=post_create.title,
        body=post_create.body,
        author_id=current_user.id,
        author_username=current_user.username,
        sentiment=sentiment
    )
    
    await db.posts.insert_one(post.dict())
    
    # Broadcast new post to WebSocket connections
    await manager.broadcast(json.dumps({
        "type": "new_post",
        "post": {
            "id": post.id,
            "title": post.title,
            "body": post.body,
            "author_username": post.author_username,
            "created_at": post.created_at.isoformat(),
            "sentiment": sentiment.dict()
        }
    }))
    
    return PostResponse(
        id=post.id,
        title=post.title,
        body=post.body,
        author_username=post.author_username,
        created_at=post.created_at,
        sentiment=sentiment
    )

@api_router.get("/posts", response_model=List[PostResponse])
async def get_posts():
    posts = await db.posts.find().sort("created_at", -1).to_list(100)
    return [PostResponse(
        id=post["id"],
        title=post["title"],
        body=post["body"],
        author_username=post["author_username"],
        created_at=post["created_at"],
        sentiment=SentimentAnalysis(**post["sentiment"]) if post.get("sentiment") else None
    ) for post in posts]

# Dashboard Routes
@api_router.get("/dashboard/stats")
async def get_dashboard_stats():
    # Get all posts with sentiment
    posts = await db.posts.find({"sentiment": {"$exists": True}}).to_list(1000)
    
    if not posts:
        return {
            "sentiment_distribution": {"Positive": 0, "Neutral": 0, "Negative": 0},
            "sentiment_over_time": [],
            "trending_keywords": []
        }
    
    # Calculate sentiment distribution
    sentiment_counts = {"Positive": 0, "Neutral": 0, "Negative": 0}
    for post in posts:
        label = post["sentiment"]["label"]
        sentiment_counts[label] = sentiment_counts.get(label, 0) + 1
    
    # Sentiment over time (last 24 hours, hourly buckets)
    from collections import defaultdict
    hourly_sentiments = defaultdict(lambda: {"Positive": 0, "Neutral": 0, "Negative": 0})
    
    for post in posts:
        created_at = post["created_at"]
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
        
        hour_key = created_at.strftime("%Y-%m-%d %H:00")
        sentiment_label = post["sentiment"]["label"]
        hourly_sentiments[hour_key][sentiment_label] += 1
    
    sentiment_timeline = []
    for hour, sentiments in sorted(hourly_sentiments.items()):
        sentiment_timeline.append({
            "time": hour,
            "Positive": sentiments["Positive"],
            "Neutral": sentiments["Neutral"],
            "Negative": sentiments["Negative"]
        })
    
    # Extract trending keywords (simple word frequency)
    from collections import Counter
    import re
    
    all_text = " ".join([f"{post['title']} {post['body']}" for post in posts])
    words = re.findall(r'\b\w{4,}\b', all_text.lower())  # Words with 4+ chars
    
    # Filter out common words
    stop_words = {"this", "that", "with", "have", "will", "been", "from", "they", "them", "were", "been", "their", "said", "each", "which", "their", "time", "will", "about", "would", "there", "could", "other", "after", "first", "well", "water", "been", "call", "who", "its", "now", "find", "long", "down", "day", "did", "get", "has", "him", "his", "how", "man", "new", "now", "old", "see", "two", "way", "who", "boy", "did", "its", "let", "put", "say", "she", "too", "use"}
    
    filtered_words = [word for word in words if word not in stop_words]
    trending_keywords = Counter(filtered_words).most_common(10)
    
    return {
        "sentiment_distribution": sentiment_counts,
        "sentiment_over_time": sentiment_timeline[-24:],  # Last 24 hours
        "trending_keywords": [{"word": word, "count": count} for word, count in trending_keywords]
    }

# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Echo back or handle specific commands
            await websocket.send_text(f"Message received: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()