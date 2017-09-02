import os
import time
import concurrent
import asyncio
import logging
import shutil


class Latest(object):
    log = logging.getLogger('dropdark')

    def __init__(self, config, loop, input):
        self.loop = loop
        self.input = input
        self.output = asyncio.Queue()

    async def run(self):
        next = 0
        while True:
            filename = await self.input.get()
            # don't go faster than every 3 seconds
            if time.time() > next:
                shutil.copyfile(filename, "latest.jpg")
                next = time.time() + 3
            await self.output.put(filename)
            self.input.task_done()

