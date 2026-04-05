import os
import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from . import db
from .routers import verses, graph, strongs, crossrefs, hermeneutics, search, explore, journal, confessions


@asynccontextmanager
async def lifespan(app: FastAPI):
    await db.init_db_pool()
    try:
        yield
    finally:
        await db.close_db_pool()


app = FastAPI(
    title="Hermeneutica Explorer API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "https://hermeneutica.xyz", "https://web-seven-delta-16.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
_web_dir = Path(__file__).resolve().parent.parent
data_dir = _web_dir / "public" / "data"
if data_dir.exists():
    app.mount("/data", StaticFiles(directory=str(data_dir)), name="data")

# Include routers (they already have prefixes defined)
app.include_router(verses.router, prefix="/api")
app.include_router(strongs.router, prefix="/api")
app.include_router(graph.router, prefix="/api")
app.include_router(crossrefs.router, prefix="/api")
app.include_router(hermeneutics.router, prefix="/api")
app.include_router(search.router, prefix="/api")
app.include_router(explore.router, prefix="/api")
app.include_router(journal.router, prefix="/api")
app.include_router(confessions.router, prefix="/api")


@app.get("/api/health")
async def health_check():
    return {"status": "ok"}


class ContactRequest(BaseModel):
    name: str
    email: str
    message: str


@app.post("/api/contact")
async def send_contact(req: ContactRequest):
    api_key = os.getenv("RESEND_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="Email service not configured")

    # Sanitize
    name = req.name.strip()[:200]
    email = req.email.strip()[:200]
    message = req.message.strip()[:5000]

    if not name or not email or not message:
        raise HTTPException(status_code=400, detail="All fields required")

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://api.resend.com/emails",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "from": "Hermeneutica <andrew@automate-capture.com>",
                "to": [os.getenv("CONTACT_EMAIL", "andrew@automate-capture.com")],
                "reply_to": email,
                "subject": f"[Hermeneutica] Message from {name}",
                "html": f"""
                    <div style="font-family: system-ui, sans-serif; max-width: 600px;">
                        <h2 style="color: #E8A838;">New message from Hermeneutica Explorer</h2>
                        <p><strong>From:</strong> {name} ({email})</p>
                        <hr style="border: none; border-top: 1px solid #eee; margin: 16px 0;" />
                        <p style="white-space: pre-wrap; line-height: 1.6;">{message}</p>
                        <hr style="border: none; border-top: 1px solid #eee; margin: 16px 0;" />
                        <p style="color: #999; font-size: 12px;">Sent from hermeneutica.xyz contact form</p>
                    </div>
                """,
            },
        )
        if resp.status_code >= 400:
            raise HTTPException(status_code=500, detail="Failed to send email")

    return {"success": True}
