import asyncio

# Minimal stub for MCPServer to fix import error
class MCPServer:
    def __init__(self):
        self._should_stop = asyncio.Event()

    async def run(self):
        # Block forever unless stop is called
        await self._should_stop.wait()

    def stop(self):
        self._should_stop.set()
