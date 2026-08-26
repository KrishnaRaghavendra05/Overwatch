"""MCP tool server for the claims dashboard.

Exposes read_flag, list_flags, write_flag, and retract_flag
as MCP tools for the TrueForge agent harness. write_flag and
retract_flag are gated by interrupt_config in agent.json
(require_approval: true).
"""

import json
import logging
import sys
from datetime import datetime

from agent.models.dashboard import (
    ChangeFlag,
    DashboardWritePayload,
)
from agent.models.imagery import BoundingBox
from dashboard.read import list_flags, read_flag
from dashboard.write import write_flag

logger = logging.getLogger(__name__)

TOOLS = {
    "read_flag": {
        "description": "Read a single flag record by record_id.",
        "parameters": {
            "type": "object",
            "properties": {
                "record_id": {"type": "string"},
            },
            "required": ["record_id"],
        },
    },
    "list_flags": {
        "description": "List all flag records in the dashboard.",
        "parameters": {"type": "object", "properties": {}},
    },
    "write_flag": {
        "description": (
            "Write an approved change flag to the live dashboard. "
            "CONSEQUENTIAL: requires human approval via TrueForge "
            "interrupt_config before execution."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "area": {
                    "type": "object",
                    "properties": {
                        "min_lon": {"type": "number"},
                        "min_lat": {"type": "number"},
                        "max_lon": {"type": "number"},
                        "max_lat": {"type": "number"},
                    },
                },
                "index_type": {"type": "string"},
                "delta_ndvi_scale": {"type": "number"},
                "severity": {"type": "string"},
                "report_text": {"type": "string"},
                "approved_by": {"type": "string"},
            },
            "required": [
                "area",
                "index_type",
                "delta_ndvi_scale",
                "severity",
                "report_text",
                "approved_by",
            ],
        },
    },
    "retract_flag": {
        "description": (
            "Retract an existing flag record. CONSEQUENTIAL: "
            "requires human approval via TrueForge interrupt_config."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "record_id": {"type": "string"},
                "approved_by": {"type": "string"},
            },
            "required": ["record_id", "approved_by"],
        },
    },
}


def handle_read_flag(params: dict) -> dict:
    """Read single flag."""
    resp = read_flag(params["record_id"])
    if not resp:
        return {"error": "Record not found"}
    return resp.model_dump(mode="json")


def handle_list_flags(params: dict) -> dict:
    """List all flags."""
    flags = list_flags()
    return {
        "flags": [f.model_dump(mode="json") for f in flags],
        "count": len(flags),
    }


def handle_write_flag(params: dict) -> dict:
    """Write approved flag — gated by TrueForge human approval."""
    area = BoundingBox(**params["area"])
    flag = ChangeFlag(
        area=area,
        detected_at=datetime.now(),
        index_type=params["index_type"],
        delta_ndvi_scale=params["delta_ndvi_scale"],
        severity=params["severity"],
        report_text=params["report_text"],
    )
    payload = DashboardWritePayload(
        flag=flag,
        approved_by=params["approved_by"],
        approved_at=datetime.now(),
        action="file",
    )
    resp = write_flag(payload)
    return resp.model_dump(mode="json")


def handle_retract_flag(params: dict) -> dict:
    """Retract existing flag — gated by TrueForge human approval."""
    existing = read_flag(params["record_id"])
    if not existing:
        return {"error": "Record not found"}
    if existing.flag is None:
        return {"error": "Cannot reconstruct flag from DB"}

    payload = DashboardWritePayload(
        flag=existing.flag,
        approved_by=params["approved_by"],
        approved_at=datetime.now(),
        action="retract",
    )
    resp = write_flag(payload)
    return resp.model_dump(mode="json")


HANDLERS = {
    "read_flag": handle_read_flag,
    "list_flags": handle_list_flags,
    "write_flag": handle_write_flag,
    "retract_flag": handle_retract_flag,
}


def main() -> None:
    """MCP stdio server loop for dashboard tools."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        stream=sys.stderr,
    )
    logger.info("MCP Dashboard Server starting...")

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

        response = {
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": result,
        }
        sys.stdout.write(json.dumps(response) + "\n")
        sys.stdout.flush()


if __name__ == "__main__":
    main()
