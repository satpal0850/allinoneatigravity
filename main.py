from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse, RedirectResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates # type: ignore
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import os
import httpx # type: ignore

from downloader import extract_media # type: ignore
from i18n import get_translation, translations # type: ignore

app = FastAPI(
    title="All-in-One Video Downloader API",
    description="API to download media from Instagram, Pinterest, TikTok, Bluesky, Twitch, and Snapchat.",
    version="1.0.0"
)

# Enable CORS (useful if frontend is served separately during dev)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class DownloadRequest(BaseModel):
    url: str
    format: str = "video"  # "video" or "audio"

@app.post("/api/download")
async def download_media(request: DownloadRequest):
    try:
        url = request.url.strip()
        if not url:
            raise HTTPException(status_code=400, detail="URL is required")

        result = extract_media(url, request.format)
        
        if result.get("error"):
            raise HTTPException(status_code=400, detail=result["error"])
            
        return JSONResponse(content=result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/proxy_download")
async def proxy_download(url: str, ext: str = "mp4", title: str = "media"):
    async def stream_file():
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            async with client.stream("GET", url) as response:
                if response.status_code != 200:
                    yield b""
                    return
                async for chunk in response.aiter_bytes():
                    yield chunk

    # Ensure safe filename
    safe_title = "".join(c for c in title if c.isalnum() or c in " _-").strip() or "download"
    headers = {
        "Content-Disposition": f'attachment; filename="{safe_title}.{ext}"'
    }
    return StreamingResponse(stream_file(), media_type="application/octet-stream", headers=headers)

# Ensure static directory exists
os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=RedirectResponse)
async def root():
    return RedirectResponse(url="/en/")

@app.get("/{lang}/", response_class=HTMLResponse)
async def home_page(request: Request, lang: str):
    return render_page(request, lang, "all")

@app.get("/{lang}/contact", response_class=HTMLResponse)
async def contact_page(request: Request, lang: str):
    t = get_translation(lang)
    return templates.TemplateResponse("contact.html", {
        "request": request,
        "lang": t,
        "all_langs": translations,
        "is_home": False,
        "page_title": "Contact Us",
        "page_desc": "Get in touch with the video downloader team.",
        "platform_path": "contact"
    })

@app.get("/{lang}/{platform}", response_class=HTMLResponse)
async def platform_page(request: Request, lang: str, platform: str):
    valid_platforms = ["instagram", "tiktok", "snapchat", "all"]
    if platform not in valid_platforms:
        return RedirectResponse(url=f"/{lang}/")
    return render_page(request, lang, platform)

def render_page(request: Request, lang: str, platform: str):
    t = get_translation(lang)
    titles = {
        "all": (t.get("heroTitle"), t.get("heroSubtitle")),
        "instagram": (t.get("igTitle"), t.get("igSub")),
        "tiktok": (t.get("ttTitle"), t.get("ttSub")),
        "snapchat": (t.get("snapTitle"), t.get("snapSub"))
    }
    
    title_text, desc_text = titles.get(platform, titles["all"])
    
    path_suffix = "" if platform == "all" else platform
    
    return templates.TemplateResponse("index.html", {
        "request": request,
        "lang": t,
        "all_langs": translations,
        "platform": platform,
        "is_home": True,
        "page_title": title_text,
        "page_desc": desc_text,
        "platform_path": path_suffix
    })

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
