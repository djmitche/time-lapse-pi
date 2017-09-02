import logging
import asyncio
import yaml

class Config(object):
    log = logging.getLogger('config')

    def __init__(self):
        self.last_cfg = {}
        self.reload()

    async def run(self):
        while True:
            await asyncio.sleep(10)
            self.reload()

    def reload(self):
        cfg = yaml.load(open("config.yml"))
        for c, v in cfg.items():
            if self.last_cfg.get(c) != v:
                self.log.warning("setting %s to %s", c, v)
        self.last_cfg = cfg
        self.__dict__.update(cfg)
