import yaml

class Config(object):

    def __init__(self):
        cfg = yaml.load(open("config.yml"))
        self.__dict__.update(cfg)
