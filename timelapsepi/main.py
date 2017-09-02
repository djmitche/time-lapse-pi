import sys
import os
import asyncio
import logging

from . import (
    capture,
    dropdark,
    upload,
    config,
)


def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)-15s %(message)s')
    loop = asyncio.get_event_loop()

    cfg = config.Config()
    if not os.path.isdir(cfg.staging_dir):
        os.makedirs(cfg.staging_dir)

    if len(sys.argv) < 2:
        raise Exception("USAGE: time-lapse-pi capture")

    if sys.argv[1] == 'capture':
        cap = capture.Capture(cfg, loop)
        asyncio.ensure_future(cap.run())

        dropd = dropdark.DropDark(cfg, loop, cap.output)
        asyncio.ensure_future(dropd.run())

        upl = upload.Upload(cfg, loop, dropd.output)
        asyncio.ensure_future(upl.run())

        try:
            loop.run_forever()
        except KeyboardInterrupt:
            pass
        finally:
            loop.close()
    else:
        raise Exception("Unknown subcommand " + sys.argv[1])
