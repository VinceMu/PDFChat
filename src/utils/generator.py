import asyncio
from typing import AsyncGenerator, Callable


def to_sync_generator(
    async_gen: AsyncGenerator,
    handler: Callable[[AsyncGenerator], AsyncGenerator] = None,
):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    if handler is not None:
        async_gen = handler(async_gen)
    try:
        while True:
            try:
                yield loop.run_until_complete(anext(async_gen))
            except StopAsyncIteration:
                break
    finally:
        loop.close()
