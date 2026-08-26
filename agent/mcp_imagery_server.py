"""MCP tool server for satellite imagery fetch.

Exposes fetch_imagery and list_cached_tiles as MCP tools
for the TrueForge agent harness to invoke.
"""

import json
import logging
import sys

from agent.config import CACHE_DIR
from agent.models.imagery import BoundingBox, DateRange
from agent.services.cache import get_or_fetch

logger = logging.getLogger(__name__)

TOOLS = {
    "fetch_imagery": {
        "description": (
            "Fetch Sentinel-2 optical bands (NIR, Red, Green, SCL) "
            "for a bounding box and date range. Returns spectral "
            "band arrays and cloud cover metadata."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "min_lon": {"type": "number"},
                "min_lat": {"type": "number"},
                "max_lon": {"type": "number"},
                "max_lat": {"type": "number"},
                "start_date": {
                    "type": "string",
                    "format": "date",
                },
                "end_date": {
                    "type": "string",
                    "format": "date",
                },
            },
            "required": [
                "min_lon",
                "min_lat",
                "max_lon",
                "max_lat",
                "start_date",
                "end_date",
            ],
        },
    },
    "list_cached_tiles": {
        "description": "List all cached imagery tiles on disk.",
        "parameters": {"type": "object", "properties": {}},
    },
}


def handle_fetch_imagery(params: dict) -> dict:
    """Execute fetch_imagery tool call."""
    from datetime import date

    area = BoundingBox(
        min_lon=params["min_lon"],
        min_lat=params["min_lat"],
        max_lon=params["max_lon"],
        max_lat=params["max_lat"],
    )
    dr = DateRange(
        start=date.fromisoformat(params["start_date"]),
        end=date.fromisoformat(params["end_date"]),
    )
    resp = get_or_fetch(area, dr)
    return resp.model_dump(mode="json")


def handle_list_cached(params: dict) -> dict:
    """List cached tiles."""
    tiles = []
    if CACHE_DIR.exists():
        for f in sorted(CACHE_DIR.glob("*.json")):
            tiles.append(f.stem)
    return {"cached_tiles": tiles, "count": len(tiles)}


HANDLERS = {
    "fetch_imagery": handle_fetch_imagery,
    "list_cached_tiles": handle_list_cached,
}


def main() -> None:
    """MCP stdio server loop.

    Reads JSON-RPC messages from stdin, dispatches to handlers,
    writes responses to stdout. This is the standard MCP
    transport protocol that TrueForge speaks.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        stream=sys.stderr,
    )
    logger.info("MCP Imagery Server starting...")

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue

        method = msg.get("method", "")
        msg_id = msg.get("id")
        params = msg.get("params", {})

        if method == "tools/list":
            result = {"tools": [{"name": k, **v} for k, v in TOOLS.items()]}
        elif method == "tools/call":
            tool_name = params.get("name", "")
            tool_args = params.get("arguments", {})
            handler = HANDLERS.get(tool_name)
            if handler:
                try:
                    result = handler(tool_args)
                except Exception as e:
                    result = {"error": str(e)}
            else:
                result = {"error": f"Unknown tool: {tool_name}"}
        else:
            result = {"error": f"Unknown method: {method}"}

        response = {"jsonrpc": "2.0", "id": msg_id, "result": result}
        sys.stdout.write(json.dumps(response) + "\n")
        sys.stdout.flush()


if __name__ == "__main__":
    main()
