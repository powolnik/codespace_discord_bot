import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import google.generativeai as genai
import asyncio
from gtts import gTTS
import discord.utils
from discord.sinks import Sink

import whisper # Add this line
import numpy as np # Add this line
import io # Add this line
import wave # Add this line
import audioop # Add this line

# --- Configuration and Setup ---
load_dotenv()
bot_token = os.environ.get('BOT_TOKEN') #'MTMzODQ4NTY2MzY3MDA3OTQ4OA.Gc27cI.RHEcr8wmPrKCSQk2hAA4O3THNZTMB0eTI1EBII'
gemini_api_key = os.environ.get('GEMINI_API_KEY')
chat_channel_name = 'free-chat-unstable' #os.environ.get('CHAT_CHANNEL_NAME') 

if bot_token is None:
    print("Error: Bot token not found. Set BOT_TOKEN environment variable.")
    exit()

if gemini_api_key is None:
    print("Error: Gemini API key not found. Set GEMINI_API_KEY environment variable.")
    exit()

genai.configure(api_key=gemini_api_key)

intents = discord.Intents.default()
intents.message_content = True # REQUIRED for reading message content for commands
intents.members = True # For on_member_join
intents.voice_states = True # Add this line for voice channel events/state tracking

# --- Use commands.Bot consistently ---
bot = commands.Bot(command_prefix="!", intents=intents)

# --- Load Whisper Model ---
# Models: tiny, base, small, medium, large. Larger models are more accurate but slower and require more resources.
WHISPER_MODEL_NAME = "tiny"
print(f"Loading Whisper model: {WHISPER_MODEL_NAME}...")
try:
    whisper_model = whisper.load_model(WHISPER_MODEL_NAME)
    print("Whisper model loaded successfully.")
except Exception as e:
    print(f"Error loading Whisper model: {e}")
    print("Transcription features will be unavailable.")
    whisper_model = None # Ensure it's None if loading failed
# --- End Whisper Model Load ---

# --- Helper Functions ---
def get_gemini_response(prompt: str) -> str:
    """Gets a response from the Gemini AI model."""
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(contents=prompt)

        if response.prompt_feedback.block_reason:
            print(f"Gemini response blocked: {response.prompt_feedback.block_reason}")
            return "My response was blocked due to safety concerns."

        return response.text
    except Exception as e:
        print(f"Error getting response from Gemini: {e}")
        return "Sorry, I encountered an error trying to process that."

def split_string(string, chunk_size=1900):
    """Split a string into chunks of a specified size."""
    return [string[i:i + chunk_size] for i in range(0, len(string), chunk_size)]

def generate_tts_audio(text: str, filename: str = "tts_response.mp3") -> str | None:
    """Generates TTS audio from text using gTTS and saves it."""
    try:
        tts = gTTS(text=text, lang='en') # You can change the language
        tts.save(filename)
        print(f"Generated TTS audio file: {filename}")
        return filename
    except Exception as e:
        print(f"Error generating TTS audio: {e}")
        return None

async def play_audio_in_vc(voice_channel: discord.VoiceChannel, audio_path: str, playback_rate: float = 1.0):
    """Connects to a voice channel, plays an audio file, and disconnects after playback."""
    if not voice_channel:
        print("Error: No voice channel provided for playback.")
        return

    guild = voice_channel.guild
    vc = discord.utils.get(bot.voice_clients, guild=guild)  # Get existing voice client

    try:
        # Connect or move
        if vc and vc.is_connected():
            if vc.channel != voice_channel:
                print(f"Moving voice client to {voice_channel.name}")
                await vc.move_to(voice_channel)
        else:
            print(f"Connecting to voice channel {voice_channel.name}")
            vc = await voice_channel.connect()

        if not vc:
            print("Error: Could not establish voice connection.")
            os.remove(audio_path) if os.path.exists(audio_path) else None
            return

        # Stop current playback if any
        if vc.is_playing():
            vc.stop()

        # Add these lines to construct ffmpeg options:
        ffmpeg_options = ""
        if playback_rate != 1.0:
            # Use the atempo filter for speed adjustment.
            # Note: Very large/small values might require chaining (e.g., "atempo=2.0,atempo=2.0")
            # Clamp the rate to a reasonable range (e.g., 0.5x to 3.0x) to prevent issues.
            clamped_rate = max(0.5, min(playback_rate, 3.0))
            ffmpeg_options = f'-filter:a "atempo={clamped_rate}"'
            print(f"Setting playback rate to {clamped_rate}x (requested: {playback_rate}x) using options: {ffmpeg_options}")
        # End of added lines

        print(f"Playing TTS audio: {audio_path}")
        # Modify the vc.play call to include options:
        # vc.play(discord.FFmpegPCMAudio(audio_path))
        vc.play(discord.FFmpegPCMAudio(audio_path, options=ffmpeg_options)) # Pass options here

        # **Wait for audio to finish before disconnecting**
        while vc.is_playing():
            await asyncio.sleep(1)  # Keep checking every second

        print("Finished playing TTS audio. Disconnecting...")
        await vc.disconnect()
        os.remove(audio_path) if os.path.exists(audio_path) else None  # Cleanup

    except discord.ClientException as e:
        print(f"Discord client error: {e}")
    except Exception as e:
        print(f"Error during voice playback: {e}")
    finally:
        if vc and vc.is_connected():
            await vc.disconnect()  # Ensure disconnection


async def handle_transcription(user: discord.User, text: str):
    """Callback function to handle the transcribed text."""
    if text and text.strip(): # Avoid printing empty transcriptions
        print(f"Transcription for {user.name} ({user.id}): {text.strip()}")
    else:
        print(f"Received empty transcription for {user.name} ({user.id})")
# End of callback function


# Add the WhisperSink class definition:
class WhisperSink(Sink):
    """A sink that buffers audio per user and transcribes using Whisper."""

    # Discord sends audio in 48kHz, 16-bit, stereo PCM format.
    DISCORD_SAMPLE_RATE = 48000
    DISCORD_CHANNELS = 2
    DISCORD_BYTES_PER_SAMPLE = 2  # 16-bit = 2 bytes

    # Whisper expects 16kHz, single-channel (mono), float32 audio.
    WHISPER_SAMPLE_RATE = 16000

    # Buffer audio for this many seconds before transcribing
    BUFFER_DURATION_SECONDS = 2

    # Calculate buffer size limit in bytes
    BUFFER_LIMIT_BYTES = (
        DISCORD_SAMPLE_RATE * DISCORD_CHANNELS * DISCORD_BYTES_PER_SAMPLE * BUFFER_DURATION_SECONDS
    )

    def __init__(self, transcription_callback):
        super().__init__()
        self.user_audio_buffers = {}  # Stores bytes data per user ID
        self.transcription_callback = transcription_callback
        self.loop = asyncio.get_running_loop()
        print(f"WhisperSink initialized. Buffering for {self.BUFFER_DURATION_SECONDS} seconds.")
        if not whisper_model:
             print("WARNING: Whisper model not loaded. Sink will not transcribe.")

    def write(self, data, user):
        """Called by discord.py when audio data is received."""
        if not user or not whisper_model: # Ignore if no user or model failed to load
            return

        if user.id not in self.user_audio_buffers:
            self.user_audio_buffers[user.id] = io.BytesIO()
            # print(f"Created buffer for user {user.id}")

        buffer = self.user_audio_buffers[user.id]
        buffer.write(data)

        # Check if buffer exceeds duration limit
        if buffer.tell() >= self.BUFFER_LIMIT_BYTES:
            # print(f"Buffer limit reached for user {user.id}. Scheduling transcription.")
            # Get buffered data, create a copy for processing
            buffer.seek(0)
            audio_data_copy = buffer.read()

            # Clear the buffer for this user immediately
            buffer.seek(0)
            buffer.truncate()

            # Schedule transcription task (don't block the write method)
            self.loop.create_task(self.process_transcription(audio_data_copy, user))

    async def process_transcription(self, pcm_data: bytes, user: discord.User):
        """Converts audio and runs transcription in an executor."""
        try:
            # 1. Convert stereo PCM to mono PCM
            # audioop requires width (bytes per sample), rate, data, and state
            mono_data, _ = audioop.ratecv(pcm_data, self.DISCORD_BYTES_PER_SAMPLE, self.DISCORD_CHANNELS,
                                          self.DISCORD_SAMPLE_RATE, self.WHISPER_SAMPLE_RATE, None)
            # After ratecv, data is still stereo if input was stereo, but at the new rate.
            # Now convert to mono.
            mono_data = audioop.tomono(mono_data, self.DISCORD_BYTES_PER_SAMPLE, 1, 1) # Average left and right channels

            # 2. Convert bytes to NumPy array (int16)
            audio_np = np.frombuffer(mono_data, dtype=np.int16)

            # 3. Convert int16 to float32 and normalize
            audio_fp32 = audio_np.astype(np.float32) / 32768.0 # Max value for int16 is 32767

            # 4. Run transcription in executor
            # print(f"Running transcription for user {user.id}...")
            result = await self.loop.run_in_executor(
                None,  # Default executor
                lambda: whisper_model.transcribe(audio_fp32, language="en", fp16=False) # fp16=False for CPU
            )
            transcribed_text = result.get("text", "")
            # print(f"Transcription complete for user {user.id}.")

            # 5. Call the callback with the result
            await self.transcription_callback(user, transcribed_text)

        except Exception as e:
            print(f"Error during transcription processing for user {user.id}: {e}")
            # Optionally call callback with an error message
            # await self.transcription_callback(user, "[Transcription Error]")

    def cleanup(self):
        """Called when the sink is stopped (e.g., on disconnect)."""
        print("WhisperSink cleanup called.")
        # Clear any remaining buffered data
        for user_id, buffer in self.user_audio_buffers.items():
            buffer.close()
            # print(f"Closed buffer for user {user_id}")
        self.user_audio_buffers.clear()
        super().cleanup()
# End of WhisperSink class definition


# --- Bot Events (Use @bot.event) ---
@bot.event
async def on_ready():
    """Prints a message to the console when the bot logs in."""
    print(f'Successfully logged in as: {bot.user}') # Use bot.user
    print(f'User ID: {bot.user.id}')
    print('Bot is online and ready.')
    print('------')
    # Send startup message (optional, using the bot instance)
    if bot.guilds:
        first_guild = bot.guilds[0]
        if first_guild.system_channel:
            try:
                # Add this block to check the last message:
                send_startup_message = True # Assume we should send initially
                last_message = None
                async for msg in first_guild.system_channel.history(limit=1):
                    last_message = msg
                    break # We only need the very last one

                if last_message and last_message.author.id == bot.user.id:
                    print(f"Last message in #{first_guild.system_channel.name} was from the bot. Skipping startup message.")
                    send_startup_message = False
                # End of added block

                # Wrap the existing logic in a condition:
                if send_startup_message:
                    startup_prompt = f"Generate a short, friendly message announcing that the Discord bot '{bot.user.name}' is now online and ready in the '{first_guild.name}' server."
                    print(f"Generating startup message with prompt: '{startup_prompt}'")

                    loop = asyncio.get_running_loop()
                    # Use run_in_executor for the blocking Gemini call
                    startup_message = await loop.run_in_executor(None, get_gemini_response, startup_prompt)

                    print(f"Gemini generated startup message: '{startup_message}'")
                    chunked_startup_message = split_string(startup_message, 1900) # Use chunk size < 2000
                    for chunk in chunked_startup_message:
                        await first_guild.system_channel.send(chunk)
                    print(f"Sent startup message to #{first_guild.system_channel.name} in {first_guild.name}")
                # End of conditional wrap

            except discord.Forbidden:
                # This might also trigger if the bot lacks history permissions
                print(f"Could not send startup message or check history in #{first_guild.system_channel.name} in {first_guild.name}: Missing permissions.")
            except Exception as e:
                print(f"Could not send startup message to #{first_guild.system_channel.name} in {first_guild.name}: {e}")
        else:
            print(f"Could not send startup message in {first_guild.name}: No system channel configured.")
    else:
        print("Bot is not currently in any guilds. Skipping startup message.")

@bot.event
async def on_member_join(member):
    """Sends a welcome message when a new member joins."""
    print(f'{member} has joined the server.')
    guild = member.guild
    if guild.system_channel is not None:
        try:
            welcome_message = f'Welcome {member.mention} to {guild.name}!'
            chunked_welcome_message = split_string(welcome_message, 1900) # Use chunk size < 2000
            for chunk in chunked_welcome_message:
                await guild.system_channel.send(chunk)
            print(f"Sent welcome message to {member} in #{guild.system_channel.name}")
        except discord.Forbidden:
            print(f"Could not send welcome message to {member} in #{guild.system_channel.name}: Missing permissions.")
        except Exception as e:
            print(f"Could not send welcome message to {member} in #{guild.system_channel.name}: {e}")
    else:
        print(f"Could not send welcome message to {member}: No system channel configured.")


# --- Bot Commands (Define BEFORE bot.run) ---
@bot.command(name="ask")
async def ask(ctx, *, message: str): # Use ': str' for type hint, '*' captures everything after !ask
    """Asks the Gemini model a question."""
    print(f"Received command '!ask' from {ctx.author} with message: '{message}'")

    # You might want to add a "thinking..." message here
    # await ctx.send("Thinking...")

    # Construct the prompt for Gemini using the user's message
    prompt_to_gemini = message # Basic case: just send the user's text
    # More advanced: you could potentially add context here if needed
    # E.g., prompt_to_gemini = f"User '{ctx.author.name}' asked: {message}"

    loop = asyncio.get_running_loop()
    try:
        # Call get_gemini_response with the *user's message*
        response_text = await loop.run_in_executor(None, get_gemini_response, prompt_to_gemini)
        print(f"Gemini response: {response_text[:200]}...") # Print start of response

        # --- Add TTS Playback Logic ---
        if ctx.author.voice and ctx.author.voice.channel and response_text:
            voice_channel = ctx.author.voice.channel
            print(f"User {ctx.author} is in voice channel {voice_channel.name}. Attempting TTS.")
            # Run synchronous TTS generation in executor
            audio_file = await loop.run_in_executor(None, generate_tts_audio, response_text)
            if audio_file:
                await play_audio_in_vc(voice_channel, audio_file)
            else:
                print("Skipping voice playback due to TTS generation error.")
        # --- End of TTS Playback Logic ---

        # Send the response back to the channel
        if response_text:
            # Split into chunks if necessary (Discord limit is 2000 chars)
            chunked_response = split_string(response_text, 1950) # Slightly less than 2k for safety
            for chunk in chunked_response:
                 await ctx.send(chunk)
        else:
            await ctx.send("Sorry, I couldn't get a response.")

    except Exception as e:
        print(f"Error during !ask command processing: {e}")
        await ctx.send("Sorry, an error occurred while processing your request.")

# Add the !listen command:
@bot.command(name="listen")
async def listen(ctx):
    """Joins the user's voice channel and starts listening."""
    if not ctx.author.voice:
        await ctx.send("You need to be in a voice channel to use this command.")
        return

    voice_channel = ctx.author.voice.channel
    guild = ctx.guild
    vc = discord.utils.get(bot.voice_clients, guild=guild) # Get current voice client

    try:
        if vc and vc.is_connected():
            if vc.channel == voice_channel:
                await ctx.send(f"I'm already listening in {voice_channel.name}.")
                # Optionally restart listening if needed, but for now, just confirm
                if not vc.is_listening():
                     # Replace BasicSink with WhisperSink:
                     # vc.listen(BasicSink())
                     vc.listen(WhisperSink(handle_transcription)) # Pass callback
                     print(f"Restarted listening in {voice_channel.name}")
                return
            else:
                # Move to the new channel if already connected elsewhere
                print(f"Moving from {vc.channel.name} to {voice_channel.name}")
                await vc.move_to(voice_channel)
                await ctx.send(f"Moved to {voice_channel.name} and started listening.")
        else:
            # Connect to the voice channel
            print(f"Connecting to {voice_channel.name}")
            vc = await voice_channel.connect()
            await ctx.send(f"Joined {voice_channel.name} and started listening.")

        # Start listening with our sink
        if vc and not vc.is_listening():
             print("Starting listener...")
             # Replace BasicSink with WhisperSink:
             # vc.listen(BasicSink())
             vc.listen(WhisperSink(handle_transcription)) # Pass callback
        elif vc:
             print("Listener already active.")

    except discord.ClientException as e:
        await ctx.send(f"Error connecting or moving: {e}")
        print(f"Discord client error during !listen: {e}")
    except Exception as e:
        await ctx.send("An unexpected error occurred while trying to listen.")
        print(f"Error during !listen: {e}")
# End of !listen command

# Add the !stoplisten command:
@bot.command(name="stoplisten")
async def stoplisten(ctx):
    """Stops listening and disconnects from the voice channel."""
    vc = discord.utils.get(bot.voice_clients, guild=ctx.guild) # Find voice client in this guild

    if vc and vc.is_connected():
        print(f"Disconnecting from {vc.channel.name}...")
        # The sink's cleanup() method should be called automatically by stop_listening()
        # which is called internally by disconnect().
        await vc.disconnect()
        await ctx.send("Stopped listening and left the voice channel.")
    else:
        await ctx.send("I'm not currently in a voice channel in this server.")
# End of !stoplisten command


@bot.event
async def on_message(message):
    """Responds to messages in the chat_channel_name channel using Gemini."""
    # Ignore messages sent by the bot itself
    if message.author == bot.user:
        return

    # Check if the message is in the chat_channel_name channel
    if message.channel.name == chat_channel_name:
        print(f"Received message in #discussion from {message.author}: '{message.content}'")

        # Get the event loop
        loop = asyncio.get_running_loop()
        try:
            # Generate response using Gemini (run synchronous function in executor)
            prompt = message.content # Use the message content as the prompt
            response_text = await loop.run_in_executor(None, get_gemini_response, prompt)
            print(f"Gemini response for #discussion: {response_text[:200]}...")

            # Send the response back to the chat_channel_name channel
            if response_text:
                chunked_response = split_string(response_text, 1950)
                for chunk in chunked_response:
                    await message.channel.send(chunk) # Send to the same channel
            else:
                # Optional: Send a message if Gemini returned nothing or an error message handled internally
                # await message.channel.send("Sorry, I couldn't generate a response for that.")
                pass # Or just do nothing

        except discord.Forbidden:
            print(f"Could not send response to #{message.channel.name}: Missing permissions.")
        except Exception as e:
            print(f"Error processing message in #discussion: {e}")
            # Optional: Notify the channel about the error
            # await message.channel.send("Sorry, an error occurred while trying to respond.")

    # Important: Process commands after handling the message event
    # This allows commands like !ask to still work even if on_message is defined.
    await bot.process_commands(message)

# --- Run the Bot (Use bot.run) ---
print("Attempting to connect to Discord...")
try:
    bot.run(bot_token) # Run the commands.Bot instance
except discord.LoginFailure:
    print("\nERROR: Login failed. The token provided is likely invalid.")
except Exception as e:
    print(f"\nERROR: An unexpected error occurred while running the bot: {e}")
