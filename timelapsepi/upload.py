import os
import concurrent
import asyncio
import logging
import boto3


class Upload(object):
    log = logging.getLogger('upload')

    def __init__(self, config, loop, input):
        self.config = config
        self.loop = loop
        self.input = input

        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=config.upload_parallelism)

        s3 = boto3.resource(
            's3',
            region_name=config.aws_region,
            aws_access_key_id=config.aws_access_key_id,
            aws_secret_access_key=config.aws_secret_access_key)
        self.bucket = s3.Bucket(config.aws_bucket)

    async def run(self):
        # stuff any pre-existing files in the staging_dir into the queue
        for f in os.listdir(self.config.staging_dir):
            filename = os.path.join(self.config.staging_dir, f)
            await self.input.put(filename)

        net_failures = 0
        while True:
            filename = await self.input.get()
            if not os.path.exists(filename):
                self.input.task_done()
                continue
            fut = self.loop.run_in_executor(self.executor, self.upload, filename)

            @fut.add_done_callback
            def uploaded(fut):
                nonlocal net_failures
                try:
                    fut.result()
                except Exception:
                    net_failures += 1
                    self.log.exception("while uploading")
                    # try this again later, but more later than not if we're having issues..
                    self.loop.call_later(min(net_failures, 120), lambda: self.input.put_nowait(filename))
                else:
                    if net_failures > 0:
                        net_failures -= 1
                self.input.task_done()

    def upload(self, filename):
        obj = self.bucket.Object(self.config.aws_object_prefix + os.path.basename(filename))
        obj.upload_file(filename)
        self.log.info("uploaded %s", filename)
        try:
            os.unlink(filename)
        except Exception:
            pass
