import sys
import os
import asyncio
import logging
from contextlib import suppress

from . import (
    capture,
    latest,
    dropdark,
    upload,
    config,
)


def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)-15s %(message)s')
    loop = asyncio.get_event_loop()

    cfg = config.Config()
    asyncio.ensure_future(cfg.run())

    if not os.path.isdir(cfg.staging_dir):
        os.makedirs(cfg.staging_dir)

    if len(sys.argv) < 2:
        raise Exception("USAGE: time-lapse-pi capture")

    if sys.argv[1] == 'capture':
        cap = capture.Capture(cfg, loop)
        asyncio.ensure_future(cap.run())

        lat = latest.Latest(cfg, loop, cap.output)
        asyncio.ensure_future(lat.run())

        dropd = dropdark.DropDark(cfg, loop, lat.output)
        asyncio.ensure_future(dropd.run())

        upl = upload.Upload(cfg, loop, dropd.output)
        asyncio.ensure_future(upl.run())

        try:
            loop.run_forever()
        except KeyboardInterrupt:
            pass
        finally:
            for t in asyncio.Task.all_tasks():
                t.cancel()
                with suppress(asyncio.CancelledError):
                    loop.run_until_complete(t)
            loop.close()
    else:
        raise Exception("Unknown subcommand " + sys.argv[1])
