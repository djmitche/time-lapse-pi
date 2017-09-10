import os
import re
import asyncio
import shutil
import logging
import time
import collections

class Encode(object):
    log = logging.getLogger('capture')

    def __init__(self, config, loop):
        self.config = config
        self.loop = loop

    async def enumerate_images(self):
        """Enumerate all images under imgdir, with by their (float) timestamp,
        in order.  This assumes that filenames end with
        "-<timestamp>.<frac>.jpg"."""
        self.log.info("enumerating images in img_dir")
        r = re.compile('-([0-9]+\.[0-9]+)\.jpg$')
        images = []
        for dirname, dirs, files in os.walk(self.config.img_dir):
            for file in files:
                # TODO: filter zero-length files
                filename = os.path.join(dirname, file)
                mo = r.search(filename)
                if not mo:
                    print("skipping", filename)
                    continue
                timestamp = float(mo.group(1))
                images.append((timestamp, filename))
            await asyncio.sleep(0)
        return sorted(images)

    async def make_intervals(self, images):
        """Given the output of enumerate_images, divide it into "intervals"
        which have more than 60s between them"""
        self.log.info("calculating intervals")
        intervals = []
        cur = None
        last_ts = 0
        for frm in images:
            ts = frm[0]
            if ts - last_ts > 60:
                cur = []
                intervals.append(cur)
            last_ts = ts
            cur.append(frm)
        # drpo really short intervals
        return [inter for inter in intervals if len(inter) > 5]

    async def render_interval(self, inter):
        name = time.strftime("%Y-%m-%d-%H:%M:%S", time.localtime(int(inter[0][0])))
        
        video_file = os.path.join(self.config.video_dir, "%s.%s" % (name, self.config.ffmpeg_output_extension))
        if os.path.exists(video_file):
            self.log.warning("video file %s already exists - not re-creating", video_file)
            return

        # determine the frame period (1/fps) for this interval by looking for
        # the most common inter-frame time
        deltas = collections.defaultdict(int)
        for i, frame2 in enumerate(inter[1:]):
            frame1 = inter[i]
            deltas[frame2[0] - frame1[0]] += 1
        deltas = sorted((v, k) for k, v in deltas.items())
        period = deltas[-1][1]
        self.log.info("frame period for interval %s: %2.2f", name, period)

        basedir = os.path.join(self.config.staging_dir, "encode", name)
        if os.path.exists(basedir):
            shutil.rmtree(basedir)
        os.makedirs(basedir)
        try:
            # hard-link each frame into a working directory with a integer-indexed
            # filaneme, since that is what ffmpeg wants
            start = inter[0][0]
            end = inter[-1][0]
            skip_count = 0
            src_idx = -1
            frame_count = int(1 + (end - start) / period)
            for frame_num in range(0, frame_count):
                frame_time = start + period * frame_num
                next_src = src_idx + 1
                if next_src < len(inter) and inter[next_src][0] <= frame_time:
                    src_idx = next_src
                else:
                    skip_count += 1
                os.link(inter[src_idx][1], os.path.join(basedir, "frame%d.jpg" % frame_num))
            if skip_count:
                self.log.info("filled in %d missing frames out of %d in %s", skip_count, frame_count, name)

            # now invoke ffmpeg
            self.log.info("encoding %s with ffmpeg (%d frames)", name, frame_count)
            tmp_video_file = video_file.replace(
                    '.' + self.config.ffmpeg_output_extension,
                    '-temp.' + self.config.ffmpeg_output_extension)
            if os.path.exists(tmp_video_file):
                os.unlink(tmp_video_file)
            args = [
                'ffmpeg',
                '-r', str(int(1 / period)),
                '-f', 'image2',
            ]
            args.extend(self.config.ffmpeg_input_options)
            args.extend([
                '-i', os.path.join(basedir, 'frame%d.jpg'),
            ])
            args.extend(self.config.ffmpeg_output_options)
            args.append(tmp_video_file)
            try:
                proc = await asyncio.subprocess.create_subprocess_exec(
                    *args,
                    stdin=open("/dev/null"),
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE)
                stdout, stderr = await proc.communicate()
                if proc.returncode != 0:
                    raise Exception("ffmpeg failed:\n{}\n{}".format(
                        stdout.decode('utf-8'), stderr.decode('utf-8')))
            except Exception:
                if os.path.exists(tmp_video_file):
                    os.unlink(tmp_video_file)
                raise
            os.rename(tmp_video_file, video_file)
            self.log.info("encoding complete: %s", video_file)
        finally:
            shutil.rmtree(basedir)

    async def run(self):
        if not os.path.exists(self.config.video_dir):
            os.makedirs(self.config.video_dir)

        images = await self.enumerate_images()
        intervals = await self.make_intervals(images)

        await asyncio.gather(*(self.render_interval(inter) for inter in intervals))
