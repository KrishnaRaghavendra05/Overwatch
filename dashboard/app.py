import logging

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from dashboard.db import init_db
from dashboard.read import list_flags, read_flag

logger = logging.getLogger(__name__)

app = FastAPI(title="Overwatch Dashboard")
templates = Jinja2Templates(directory="dashboard/templates")


@app.on_event("startup")
async def startup() -> None:
    init_db()


# status page — shows all flag records
@app.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    flags = list_flags()
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"flags": flags},
    )


# json list of all flags
@app.get("/flags")
async def flags_list() -> list:
    return [f.model_dump() for f in list_flags()]


# json detail for single flag
@app.get("/flags/{record_id}")
async def flag_detail(record_id: str) -> dict:
    return read_flag(record_id).model_dump()
