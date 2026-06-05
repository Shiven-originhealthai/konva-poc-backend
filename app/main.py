from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os
import uvicorn
from api.v1.router import api_router
from db.database import engine, Base
import models.user  # noqa: F401 - registers User model with Base
import models.thumbnail     # noqa: F401 - registers Thumbnail model with Base
import models.canvas_state  # noqa: F401 - registers CanvasState model with Base

# Comma-separated list of allowed origins.
# Override with ALLOWED_ORIGINS env var when deploying:
#   ALLOWED_ORIGINS=http://your-frontend-ip
allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    try:
        with engine.connect():
            print("✅ Database connected successfully")
        Base.metadata.create_all(bind=engine)
        print("✅ Tables created successfully")
    except Exception as e:
        print(f"❌ Database error: {e}")
    yield


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=3001)
