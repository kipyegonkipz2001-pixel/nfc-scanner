import os
import random
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from typing import Dict, List

app = FastAPI()

class SessionManager:
    def __init__(self):
        self.sessions: Dict[str, List[WebSocket]] = {}
    def generate_code(self) -> str:
        while True:
            code = f"{random.randint(100000, 999999)}"
            if code not in self.sessions:
                self.sessions[code] = []
                return code
    async def connect(self, code: str, ws: WebSocket):
        await ws.accept()
        if code not in self.sessions: self.sessions[code] = []
        self.sessions[code].append(ws)
    def disconnect(self, code: str, ws: WebSocket):
        if code in self.sessions and ws in self.sessions[code]:
            self.sessions[code].remove(ws)
            if not self.sessions[code]: del self.sessions[code]
    async def broadcast(self, code: str, message: str, sender: WebSocket):
        if code in self.sessions:
            for conn in self.sessions[code]:
                if conn != sender: await conn.send_text(message)

manager = SessionManager()

@app.get("/", response_class=HTMLResponse)
async def read_root():
    if os.path.exists("index.html"):
        with open("index.html", "r", encoding="utf-8") as file:
            return file.read()
    return "<h1>index.html not found</h1>"

@app.get("/api/new-code")
async def get_new_code():
    return {"pairing_code": manager.generate_code()}

@app.websocket("/ws/{code}")
async def websocket_endpoint(ws: WebSocket, code: str):
    await manager.connect(code, ws)
    try:
        while True:
            data = await ws.receive_text()
            await manager.broadcast(code, data, sender=ws)
    except WebSocketDisconnect:
        manager.disconnect(code, ws)
