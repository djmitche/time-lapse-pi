import os
import time
import asyncio
import logging


class Capture(object):
    log = logging.getLogger('capture')

    def __init__(self, config, loop):
        self.config = config
        self.loop = loop
        self.output = asyncio.Queue()

    async def run(self):
        # stuff any pre-existing files in the staging_dir into the queue
        for (dirpath, dirnames, filenames) in os.walk(self.config.staging_dir):
            for filename in filenames:
                filename = os.path.join(dirpath, filename)
                self.log.info("injecting found file %s", filename)
                await self.output.put(filename)

        def calc_next():
            period = self.config.capture_period
            now = time.time()
            if period:
                now -= now % period
                return now + period
            else:
                return now
        next = calc_next()

        while True:
            if self.config.capture_period > 0:
                now = next
                if next > time.time():
                    await asyncio.sleep(next - time.time())
                    next += self.config.capture_period
                else:
                    self.log.warning("capture is behind schedule by %s seconds; skipping frame(s)", time.time() - next)
                    next = calc_next()
            else:
                now = next = time.time()

            stamp = time.strftime("%Y-%m-%d/%H/%H:%M:%S", time.localtime(now))
            stamp += "-{}".format(now)
            filename = os.path.join(self.config.staging_dir, stamp + ".jpg")
            dirname = os.path.dirname(filename)
            if not os.path.exists(dirname):
                os.makedirs(dirname)
            try:
                await self.capture_image(filename)
            except Exception:
                self.log.exception("while capturing frame")
                continue

            await self.output.put(filename)

    async def capture_image(self, filename):
        """Capture an image from the webcam, writing it to the given filename."""
        proc = await asyncio.subprocess.create_subprocess_exec(
            'fswebcam', filename, *self.config.fswebcam_options,
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        stdout, stderr = await proc.communicate()
        if proc.returncode != 0:
            raise Exception("fswebcam failed:\n{}\n{}".format(
                stdout.decode('utf-8'), stderr.decode('utf-8')))
        if not os.path.exists(filename):
            # fswebcam likes to fail and exit(0)
            raise Exception("fswebcam failed:\n{}\n{}".format(
                stdout.decode('utf-8'), stderr.decode('utf-8')))
        self.log.info('captured %s', filename)
