import sys
import configparser
from functools import cache
import nest_asyncio

@cache
class essentials: # Is considered essential for the bot to run
    def __init__(self, loop=None):
        self.loop = loop
        self.get_essentials()
        self.do_essentials()

    def get_essentials(self):
        config = configparser.ConfigParser()
        config.read("config.ini")

        if "transcribe" not in config:
            print("Something is wrong with your config.ini file.")
            sys.exit(1)

        try:
            self.USE_API = config.getboolean("transcribe","use_api")
            self.TRANSCRIBE_APIKEY = config["transcribe"]["apikey"]
            self.TRANSCRIBE_AUTOMATICALLY = config.getboolean("transcribe", "automatically")
            self.TRANSCRIBE_VMS_ONLY = config.getboolean("transcribe", "voice_messages_only")
            self.LOG_LEVEL = config["logging"]["level"]
            self.LOG_FILE = config["logging"]["file"]
            self.ENABLE_STREAM_HANDLER = config.getboolean("logging", "enable_stream_handler")
        except (configparser.NoOptionError, ValueError) as e:
            print(e)
            print("Something is wrong with your config.ini file.")
            sys.exit(1)

    def do_essentials(self):
        nest_asyncio.apply(self.loop) # Apply nest_asyncio patch to the loop
        if self.USE_API and self.TRANSCRIBE_APIKEY == "0":
            print("You need to provide an API Key if you want to use the OpenAI API.")
            sys.exit(1)