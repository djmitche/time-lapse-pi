import os
import concurrent
import asyncio
import logging
from PIL import Image


class DropDark(object):
    log = logging.getLogger('dropdark')

    def __init__(self, config, loop, input):
        self.loop = loop
        self.input = input
        self.output = asyncio.Queue()

        self.threshold = config.darkness_threshold

    def darkness(self, filename):
        img = Image.open(filename)
        img = img.convert('L')
        hist = img.histogram()
        return 98 * sum(hist[:16]) / sum(hist)

    async def run(self):
        while True:
            filename = await self.input.get()
            darkness = self.darkness(filename)
            self.log.info('darkness of %s = %s', filename, darkness)
            if darkness <= self.threshold:
                await self.output.put(filename)
            else:
                os.unlink(filename)
            self.input.task_done()
