# discord-voice-message-transcriber

Discord.py bot that transcribes voice messages using OpenAI Whisper

<img width="618" alt="Screenshot 2023-04-15 at 11 38 56 PM" src="https://user-images.githubusercontent.com/44641166/232242082-af33cc32-e479-4bf8-aef6-80e6f3453226.png">

# Get Started

To use the bot, you will first need to install [Python](https://python.org). Python 3.10 is recommended as it's the easiest to set up. 3.11 also works and can provide some speedup, but you may need to install a pre-release version of numba using `pip install --pre numba`.

You can install the needed dependencies by doing `pip install -r requirements.txt`.

You will also need a bot token (acquirable at the [Discord Developer Portal](https://discord.com/developers/applications)), which you will need to add to the `.env` file after `BOT_TOKEN=`. Make sure your bot has the Message Content intent, or it won't be able to read any voice messages.

You also need a MariaDB/MySQL database (either of them). Once all the details have been acquired then proceed to copy the `sample.env` file and rename it to `.env` and fill in the details.

Finally, in the `config.ini` file, you can change some settings that alter how the bot works. The comments in the file should suffice for that purpose

# Contribute & Other Stuff

Sorry for the spaghetti code, I frankly have no idea how to do voice recognition efficiently.

Feel free to make pull requests to improve stuff for the next person.

If you encounter any issues with the code, leave them in the issue tracker and someone might fix it for you.

The code is licensed under the MIT license, which probably means you can do whatever with it, so have fun :)
