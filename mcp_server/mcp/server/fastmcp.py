# mcp/server/fastmcp.py

import inspect
import json
import logging
import traceback
from functools import wraps

from mcp.server.mcp import MCPServer

log = logging.getLogger(__name__)


class ToolCallContext:
    def __init__(self, call_id, tool_name, input_data):
        self.call_id = call_id
        self.tool_name = tool_name
        self.input = input_data


def json_schema(schema):
    def decorator(fn):
        fn._tool_schema = schema
        return fn
    return decorator


def handle_tool_call(name, description):
    def decorator(func):
        @wraps(func)
        async def wrapper(self, context, input_data):
            try:
                return await func(self, context, input_data)
            except Exception as e:
                log.error(f"Tool '{name}' failed: {e}")
                log.debug(traceback.format_exc())
                raise JSONRPCError(code=-32000, message=f"Internal error in tool '{name}': {str(e)}")

        wrapper._tool_name = name
        wrapper._tool_description = description
        wrapper._tool_input_schema = getattr(func, "_tool_schema", {"type": "object"})
        return wrapper
    return decorator


class FastMCP(MCPServer):
    def __init__(self, tool_class):
        self.tool_class = tool_class
        self.tool_methods = {}
        self.tool_instance = tool_class()

        for name, member in inspect.getmembers(self.tool_instance, predicate=inspect.ismethod):
            if hasattr(member, "_tool_name"):
                tool_id = member._tool_name
                self.tool_methods[tool_id] = member

        super().__init__()

    async def list_tools(self):
        return [
            {
                "name": method._tool_name,
                "description": method._tool_description,
                "inputSchema": method._tool_input_schema,
            }
            for method in self.tool_methods.values()
        ]

    async def call_tool(self, call_id, tool_name, input_data):
        method = self.tool_methods.get(tool_name)
        if not method:
            raise JSONRPCError(code=-32601, message=f"Tool '{tool_name}' not found")

        context = ToolCallContext(call_id, tool_name, input_data)
        return await method(context, input_data)


# Add a minimal JSONRPCError for local use
class JSONRPCError(Exception):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code
        self.message = message
