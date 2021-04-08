import threading
import inspect
import asyncio


class ThreadCommand:
    def __init__(self, f, *args, **kwargs) -> None:
        self.f = f
        self.args = args
        self.kwargs = kwargs
        self.completeEvent = threading.Event()
        self.result = None
        self.timedOut = False
        self.isStopCommand = False

    def setAsStopCommand(self):
        self.isStopCommand = True

    async def execute(self):
        try:
            self.result = self.f(*self.args, **self.kwargs)
            if inspect.isawaitable(self.result):
                self.result = await self.result
                if isinstance(self.result, asyncio.Future):
                    self.result = self.result.result()
        except Exception as e:
            self.result = e
        self.completeEvent.set()
        return self.result

    def waitForResult(self, timeout=None):
        self.timedOut = not self.completeEvent.wait(timeout)
        if self.timedOut:
            raise TimeoutError("Command Timed out")
        if isinstance(self.result, Exception):
            raise self.result
        return self.result
