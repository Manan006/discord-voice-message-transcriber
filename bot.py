from discord.ext import commands
from typing import List, Optional
import discord
from discord.ext import commands
import common
import asyncio

logger = common.logger("Bot")


class Bot(commands.Bot):
    def __init__(
        self,
        *args,
        initial_extensions: List[str] = [],
        testing_guild_id: Optional[int] = None,
        **kwargs,
    ):
        logger.info("Initializing discord.py")
        super().__init__(*args, **kwargs)
        self.testing_guild_id = testing_guild_id
        self.initial_extensions = initial_extensions

    async def setup_hook(self) -> None:

        # here, we are loading extensions prior to sync to ensure we are syncing interactions defined in those extensions.
        logger.info("Loading extensions")
        for extension in self.initial_extensions:
            logger.debug(f"Loading {extension}")
            await self.load_extension(extension)

        # In overriding setup hook,
        # we can do things that require a bot prior to starting to process events from the websocket.
        # In this case, we are using this to ensure that once we are connected, we sync for the testing guild.
        # You should not do this for every guild or for global sync, those should only be synced when changes happen.
        if self.testing_guild_id:
            logger.info("Syncing guild")
            guild = discord.Object(self.testing_guild_id)
            # We'll copy in the global commands to test with:
            self.tree.copy_global_to(guild=guild)
            # followed by syncing to the testing guild.
            await self.tree.sync(guild=guild)

        # This would also be a good place to connect to our database and
        # load anything that should be in memory prior to handling events.
