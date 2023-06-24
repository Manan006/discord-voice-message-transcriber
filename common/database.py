import aiomysql
from typing import Any, Callable, Union, List
import asyncio
from .logging import logger
from .essential import essentials
import functools
import os
import dotenv
import aiofiles

dotenv.load_dotenv()

class mariadb: # Class which handles the mariadb connection. MUST BE ENDED WITH `mariadb.end()`
    def __init__(self, clean_tables: Union[None, List[str]] = [], auto_commit:bool = False) -> None:
        self.auto_commit = auto_commit
        self.loop = asyncio.get_event_loop()
        if type(clean_tables) is str: # If only one table is to be cleaned and the input is a string
            self.clean_tables = (clean_tables,)
        else:
            self.clean_tables = clean_tables

        self.essentials = essentials
        # essentials(self.loop)
        self.functools = functools
        self.logger = logger("mariadb")
        self.aiomysql = aiomysql
        self.files = aiofiles
        self.success = self.loop.run_until_complete(self.__ainit__()) # Run the async init function

    async def __ainit__(self) -> None:
        try:
            self.pool = await self.generate_mariadb_pool()
        except Exception as e:
            self.logger.error("Unable to connect to database")
            self.logger.exception(e)
            return False
        self.logger.debug("Generated mariadb pool")
        self.conn = await self.pool.acquire()
        self.logger.debug("Generated mariadb internal connection")
        self.cursor = await self.conn.cursor()
        self.logger.debug("Generated mariadb internal cursor")
        await self.init_mariadb()
        if self.clean_tables is not None: # If the clean_tables variable is requested
            await self.table_clean()
        await self.conn.commit()
        return True
    def pool_to_cursor(self, func: Callable[..., Any]): # Decorator which adds a cursor parameter to the function it is being called upon
        @self.functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any):
            conn = None
            self.logger.debug(
                "Acquiring connection from pool and cursor from connection")
            try:
                conn = await self.pool.acquire()
            except Exception as e:
                self.logger.critical(
                    "Failed to acquire connection from pool. Waiting for 5*6 seconds (5 seconds * 6 tries)")
                self.logger.exception(e)
                for i in range(6):
                    try:
                        conn = await self.pool.acquire()
                    except aiomysql.err.OperationalError as e:
                        self.logger.critical(
                            f"Failed to acquire connection from pool. Waiting for {5*(6-i)} seconds")
                        await asyncio.sleep(5)
                    else:
                        break
                if conn is None:
                    self.logger.critical(
                        "Failed to acquire connection from pool. Exiting")
            cursor = await conn.cursor()
            self.logger.debug("Running target")
            try:
                result = await func(cursor, *args, *kwargs)
            except Exception as e:
                self.logger.critical("Failed to run target")
                self.logger.exception(e)
                await cursor.close()
                conn.close()
                await self.pool.release(conn)
                return
            await conn.commit()
            await cursor.close()
            conn.close()
            await self.pool.release(conn)
            return result
        return wrapper

    async def generate_mariadb_pool(self) -> aiomysql.pool.Pool:
        self.logger.info("Initializing mariadb")
        pool = await self.aiomysql.create_pool(host=os.getenv("DB_HOST"),
                                        port=int(os.getenv("DB_PORT")),
                                        user=os.getenv("DB_USER"),
                                        password=os.getenv("DB_PASSWORD"),
                                        db=os.getenv("DB_NAME"),
                                        autocommit=self.auto_commit, # Autocommit is set to false so that the connection can be committed after the query is executed
                                        minsize=1, # Minimum number of connections in the pool
                                        maxsize=int(os.getenv("DB_CONNECTION_MAX_LIMIT")))            
        return pool

    async def end(self) -> None: # Must be ended by calling this function
        self.logger.info("Closing mariadb connection")
        await self.cursor.close()
        self.logger.debug("Closed mariadb internal cursor")
        self.conn.close()
        self.logger.debug("Closed mariadb internal connection")
        self.pool.close()
        self.logger.debug("Closed mariadb pool")
        self.logger.info("MariaDB module closed")

    async def init_mariadb(self) -> None:
        self.logger.info(("Initializing mariadb"))
        try:
            for query in await self.get_sql("init"):
                await self.cursor.execute(query)
        except Exception as e:
            self.logger.critical("Failed to create tables in mariadb")
            self.logger.exception(e)
            return
        self.logger.info("Initialized mariadb tables")

    async def table_clean(self) -> None: # Cleans the tables. Recommended to be used only in development. Recieves a list/tuple of tables to be cleaned
        self.logger.info("Cleaning tables")
        try:
            for table in self.clean_tables:
                await self.cursor.execute(f"DELETE FROM {table}")
        except Exception as e:
            self.logger.critical("Failed to clean tables")
            self.logger.exception(e)

    async def get_sql(self, name: str): # Gets the sql query from the sql folder
        self.logger.info(f"Getting sql query: {name}.sql")
        try:
            async with self.files.open(f"sql/{name}.sql", mode="r") as f:
                query: str = await f.read()
        except Exception as e:
            self.logger.critical(f"Failed to get sql query: {name}.sql")
            self.logger.exception(e)
            return tuple()
        self.logger.info(f"Got sql query: {name}.sql")
        return tuple(filter(lambda x: x != "", query.strip().split(";"))) # Returns a tuple of queries seperated by semicolons and removes empty lines
