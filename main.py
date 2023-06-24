import io
import os
import functools
import common
import discord
import speech_recognition
import pydub
from discord import Intents
from dotenv import load_dotenv
from bot import Bot

load_dotenv(".env")
BOT_TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(command_prefix="%",intents=Intents.all(),testing_guild_id=926456391831539732)
recognizer = speech_recognition.Recognizer()


essentials = common.essentials()
logger = common.logger("Bot")
if essentials.ENABLE_SQL:
	db = common.mariadb('transcriptions',True)
	if not db.success:
		logger.error("Could not connect to database. Running with SQL disabled")
		print("ERROR: Could not connect to database. Running with SQL disabled... Check logs for more information.")
		essentials.ENABLE_SQL = False
		cache = {}
else:
	cache = {}
async def transcribe_message(message):
	if len(message.attachments) == 0:
		await message.reply("Transcription failed! (No Voice Message)", mention_author=False)
		logger.debug("No attachments found in message")
		return
	if essentials.TRANSCRIBE_VMS_ONLY and message.attachments[0].content_type != "audio/ogg":
		await message.reply("Transcription failed! (Attachment not a Voice Message)", mention_author=False)
		logger.debug("Attachment is not a voice message")
		return
	
	logger.info("Transcribing message " + str(message.id))
	msg = await message.reply("✨ Transcribing...", mention_author=False)
	if essentials.ENABLE_SQL:
		await db.cursor.execute("INSERT INTO `transcriptions` (`msg_id`, `reply_link`) VALUES (%s, %s)", (message.id, msg.jump_url))
	else:
		cache[message.id] = msg.jump_url
	
	# Read voice file and converts it into something pydub can work with
	voice_file = await message.attachments[0].read()
	voice_file = io.BytesIO(voice_file)
	
	# Convert original .ogg file into a .wav file
	logger.debug("Converting .ogg file into .wav file")
	x = await bot.loop.run_in_executor(None, pydub.AudioSegment.from_file, voice_file)
	new = io.BytesIO()
	await bot.loop.run_in_executor(None, functools.partial(x.export, new, format='wav'))
	
	# Convert .wav file into speech_recognition's AudioFile format or whatever idrk
	logger.debug("Converting .wav file into speech_recognition's AudioFile format")
	with speech_recognition.AudioFile(new) as source:
		audio = await bot.loop.run_in_executor(None, recognizer.record, source)
	
	# Runs the file through OpenAI Whisper (or API, if configured in config.ini)
	if essentials.USE_API:
		logger.info("Transcribing using OpenAI Whisper API")
		try:
			result = await bot.loop.run_in_executor(None, functools.partial(recognizer.recognize_whisper_api, audio, api_key=essentials.TRANSCRIBE_APIKEY))
		except Exception as e:
			logger.error("Failed to transcribe using OpenAI Whisper API")
			logger.exception(e)
			await msg.edit(content="Transcription failed! (OpenAI Whisper API Error)")
			return
	else:
		logger.info("Transcribing using OpenAI Whisper local engine")
		result = await bot.loop.run_in_executor(None, recognizer.recognize_whisper, audio)

	if result == "":
		result = "*nothing*"
		
	# Send results + truncate in case the transcript is longer than 1900 characters
	await msg.edit(content="**Audio Message Transcription:\n** ```" + result[:1900] + ("..." if len(result) > 1900 else "") + "```")

@bot.event
async def on_message(message):
	if essentials.TRANSCRIBE_AUTOMATICALLY and message.flags.voice and len(message.attachments) == 1:
		await transcribe_message(message)

# Slash Command / Context Menu Handlers
@bot.tree.command(name="opensource")
async def open_source(interaction: discord.Interaction):
	embed = discord.Embed(
		title="Open Source",
		description="This bot is open source! You can find the source code "
					"[here](github.com/manan006/discord-voice-message-transcriber)",
		color=0x00ff00
	)
	await interaction.response.send_message(embed=embed)
	
@bot.tree.context_menu(name="Transcribe VM")
async def transcribe_contextmenu(interaction: discord.Interaction, message: discord.Message):
	if essentials.ENABLE_SQL:
		await db.cursor.execute("SELECT `reply_link` FROM `transcriptions` WHERE `msg_id` = %s",(message.id,))
		transcription_link = await db.cursor.fetchone()
		if transcription_link is not None:
			transcription_link = transcription_link[0]
	else:
		transcription_link =  cache.get(message.id)
	if transcription_link is not None:
		await interaction.response.send_message(content=transcription_link, ephemeral=True)
		return
	await interaction.response.send_message(content="Transcription started!", ephemeral=True)
	logger.debug(f"Transcription requested for message {message.id} by {interaction.user.id}")
	await transcribe_message(message)

@bot.tree.command(name="exit")
async def exit(interaction: discord.Interaction):
	if not await bot.is_owner(interaction.user):
		logger.debug(f"User {interaction.user.id} tried to exit the bot")
		await interaction.response.send_message("You are not the bot owner!", ephemeral=True)
		return
	logger.info("Exiting bot")
	await interaction.response.send_message("Exiting...", ephemeral=True)
	if essentials.ENABLE_SQL:
		await db.end()
	await bot.close()
	logger.info("Exited bot")
	
async def close_gracefully():
	logger.info("Exiting bot")
	if essentials.ENABLE_SQL:
		await db.end()
	logger.info("Exited bot")
	print("Exited bot gracefully")

if __name__ == "__main__":
	bot.run(BOT_TOKEN,close_gracefully)
