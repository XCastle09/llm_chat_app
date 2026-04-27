from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from .routers import auth, chats, ask

app = FastAPI(title="LLM Chat App")

app.include_router(auth.router)
app.include_router(chats.router)
app.include_router(ask.router)

app.mount("/static", StaticFiles(directory="app/static"), name="static")

@app.get("/")
async def root():
    return FileResponse("app/static/index.html")