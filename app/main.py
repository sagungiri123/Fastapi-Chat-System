from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.api.v1 import auth,  messages
from app.api import websocket
from app.api.v1 import auth, messages, users 

app = FastAPI()

app.include_router(auth.router, prefix="/api/v1")
app.include_router(messages.router, prefix="/api/v1")
app.include_router(websocket.router)
app.include_router(users.router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"message": "chat api running"}

app.mount("/static", StaticFiles(directory="app/static"), name="static")
