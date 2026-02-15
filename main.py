from contextlib import asynccontextmanager
from fastapi import FastAPI
import uvicorn
from api_v1.user.views import router as user_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(
    lifespan=lifespan,
    title="Smart Hotel API",
    description="API Smart Hotel",
    version="0.1.0",
)

app.include_router(router=user_router, tags=["user"], prefix="/user")

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=7777)