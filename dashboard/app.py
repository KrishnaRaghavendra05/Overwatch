import logging

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from dashboard.read import list_flags, read_flag

logger = logging.getLogger(__name__)

app = FastAPI(title="geo-change-agent dashboard")
templates = Jinja2Templates(directory="dashboard/templates")


# status page — shows all flag records
@app.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    raise NotImplementedError


# json list of all flags
@app.get("/flags")
async def flags_list() -> list:
    _ = list_flags
    raise NotImplementedError


# json detail for single flag
@app.get("/flags/{record_id}")
async def flag_detail(record_id: str) -> dict:
    _ = read_flag
    raise NotImplementedError
