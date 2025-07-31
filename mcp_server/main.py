
import logging
import time

import contextlib

from collections.abc import AsyncIterator

from mcp.server.lowlevel import Server
import mcp.types as types
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager

from starlette.applications import Starlette
from starlette.routing import Mount, Route
from starlette.responses import JSONResponse
from starlette.requests import Request
from starlette.types import Receive, Scope, Send

# Moje importy
from tools import get_all_tools, execute_tool

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def health_check(request: Request):
    return JSONResponse({
        "timestamp": time.time(),
        "status": "healthy",
        "service": "mcp server",
        "version": "0.1.0",
        "method": request.method
    })

def serve():
    server = Server("mcp-finance")

    @server.list_tools()
    async def list_tools() -> list[types.Tool]: # type: ignore[misc]
        """
        Returns a list of available tools.
        """
        return get_all_tools()
    
    @server.call_tool() 
    async def call_tool(name: str, arguments: dict): # type: ignore[misc]
        """
        Calls a specific tool with the provided name and arguments.
        """
        return await execute_tool(name, **arguments)



    # ---------------------------------
    # Streamable HTTP Server Transport
    # ---------------------------------

    # Create the session manager with our app and event store
    session_manager = StreamableHTTPSessionManager(
        app=server,
        json_response=True,  # Use JSON responses
        event_store=None,  # No resumability
        stateless=True,
    )

    # ASGI handler for streamable HTTP connections
    async def handle_streamable_http(scope: Scope, receive: Receive, send: Send) -> None:
        await session_manager.handle_request(scope, receive, send)

    @contextlib.asynccontextmanager
    async def lifespan(app: Starlette) -> AsyncIterator[None]:
        """Context manager for managing session manager lifecycle."""
        async with session_manager.run():
            logging.info("Application started with StreamableHTTP session manager!")
            try:
                yield
            finally:
                logging.info("Application shutting down...")

    starlette_app = Starlette(
        debug=True,
        routes=[
            Mount("/mcp", app=handle_streamable_http),
            Route("/health", health_check),
            ],
        lifespan=lifespan,
    )

    return starlette_app



app = serve()


if __name__ == "__main__":
    import uvicorn
    logging.info("Starting server...")
    try:
        uvicorn.run("main:app", host="0.0.0.0", port=9000, reload=True)
    except KeyboardInterrupt:
        logging.info("KeyboardInterrupt received. Cleaning up before exit...")