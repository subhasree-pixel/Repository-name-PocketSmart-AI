from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

app = FastAPI(
    title="PocketSmart AI",
    description="Your Smart Budget & Recommendation Assistant",
    version="1.0.0",
)

# Static files
app.mount(
    "/static",
    StaticFiles(directory="app/static"),
    name="static",
)

# HTML templates
templates = Jinja2Templates(directory="templates")


@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "request": request,
        },
    )


@app.get("/home-planner")
async def home_planner(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="home_planner.html",
        context={
            "request": request,
        },
    )


@app.get("/party-planner")
async def party_planner(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="party_planner.html",
        context={
            "request": request,
        },
    )


@app.get("/jewelry-planner")
async def jewelry_planner(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="jewelry_planner.html",
        context={
            "request": request,
        },
    )


@app.get("/health")
async def health():
    return {
        "status": "healthy",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=5000,
        reload=True,
    )