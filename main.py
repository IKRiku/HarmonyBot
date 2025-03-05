# libraries
import discord 
from discord.ext import commands, tasks 
import os 
from dotenv import load_dotenv  
import google.generativeai as genai  
import asyncio 
import datetime
import youtube_dl 

# environment variables from .env file
load_dotenv()

# Discord bot token
TOK = os.getenv('DISCORD_TOKEN')

# Gemini API
GEM = os.getenv('GEMINI_API_KEY')

# used to configure gemini ai
genai.configure(api_key=GEM)

# initialize model, only accepts upto 2000 characters however (from the api to the bot i mean)
mod = genai.GenerativeModel('gemini-1.5-pro-latest')

# enable all intents for the bot, not sure what it does but needed to declare intents
intents = discord.Intents.all()

# initialize the bot with a command prefix '!'
bot = commands.Bot(command_prefix='!', intents=intents)

# global variables
rem = {}  # dictionary to store reminders (key: user ID, value: list of reminders)
que = {}  # dictionary to store music queues (key: guild ID, value: list of URLs)
yt_opts = {'format': 'bestaudio/best'}  # youTube audio download
ytdl = youtube_dl.YoutubeDL(yt_opts)  # youTube downloader instance

# Event: triggered when the bot is ready and connected to Discord
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')  # Log bot's username
    #chk_rem.start()  # Start the reminder-checking loop

# Event: triggered whenever a message is sent in a channel the bot can see
@bot.event
async def on_message(msg):
    try:
        # ignore messages sent by the bot
        if msg.author == bot.user:
            return

        # check if the bot is mentioned in the message
        if bot.user.mentioned_in(msg):
            # remove the bots mention from the message to get the prompt fr ai
            prm = msg.content.replace(f'<@{bot.user.id}>', '').strip()
            # generate a response using gemini 
            res = mod.generate_content(prm)
            # send the response back to the channel
            await msg.channel.send(res.text)

        # process commands (required for commands to work)
        await bot.process_commands(msg)

    except Exception as e:
        # log any errors that occur
        print(f"Error in on_message: {e}")

# WORKS
# Command: respond with 'Pong!' when the user types '!ping'
@bot.command(name='ping')
async def ping(ctx):
    await ctx.send('Pong!')

# WORKS
# Command: Greet the user when they type '!hello'
@bot.command(name='hello')
async def hello(ctx):
    await ctx.send(f'Hello {ctx.author.mention}!')

# DOESNT WORK
# Command: Set a reminder for a specific time
@bot.command(name='remind')
async def remind(ctx, t_str: str, *, msg: str):
    try:
        # parse the time string into a datetime object
        t = datetime.datetime.strptime(t_str, '%Y-%m-%d %H:%M')
        # check if the user already has reminders
        if ctx.author.id not in rem:
            rem[ctx.author.id] = []  # initialize an empty list for reminders
        # add the new reminder to the user's list
        rem[ctx.author.id].append({'time': t, 'msg': msg})
        # confirm the reminder was set
        await ctx.send(f'Reminder set for {t.strftime("%Y-%m-%d %H:%M")}')
    except ValueError:
        # handle invalid time format
        await ctx.send('Invalid time format. Use %Y-%m-%d %H:%M')
    except Exception as e:
        # log any errors
        print(f"Error in remind: {e}")

'''
# Task: Check reminders every 60 seconds
@tasks.loop(seconds=60)
async def chk_rem():
    try:
        # Get the current time
        now = datetime.datetime.now()
        # Loop through all reminders
        for uid, u_rem in list(rem.items()):
            for r in list(u_rem):
                # Check if the reminder time has passed
                if r['time'] <= now:
                    # Fetch the user and send the reminder
                    usr = await bot.fetch_user(uid)
                    await usr.send(f'Reminder: {r["msg"]}')
                    # Remove the reminder from the list
                    rem[uid].remove(r)
            # If the user has no more reminders, remove their entry
            if not rem[uid]:
                del rem[uid]
    except Exception as e:
        # Log any errors
        print(f"Error in chk_rem: {e}")
'''

# WORKS
# Command: Create a poll with a question and options
@bot.command(name='poll')
async def poll(ctx, q: str, *opts):
    try:
        # ensure there are at least two options
        if len(opts) < 2:
            await ctx.send('Provide at least two options.')
            return

        # create an embed with the question and options
        emb = discord.Embed(title=q, description='\n'.join([f'{i+1}. {o}' for i, o in enumerate(opts)]))
        # send the embed to the channel
        msg = await ctx.send(embed=emb)

        # add reactions for each option (1⃣, 2⃣, etc.)
        for i in range(len(opts)):
            await msg.add_reaction(f'{i+1}⃣')
    except Exception as e:
        # log any errors
        print(f"Error in poll: {e}")

# WORKS
# Command: Summarize a message by its ID
@bot.command(name='summarize')
async def summarize(ctx, msg_id: int):
    try:
        # get message by its ID
        msg = await ctx.channel.fetch_message(msg_id)
        # generate a summary using the Gemini model
        sumry = mod.generate_content(f"Summarize this:\n {msg.content}")
        # send the summary to the channel
        await ctx.send(sumry.text)
    except discord.NotFound:
        # handle case where the message is not found
        await ctx.send("Message not found.")
    except Exception as e:
        # log any errors
        print(f"Error in summarize: {e}")

# Cant test
# Event: Triggered when a new member joins the server
@bot.event
async def on_member_join(mem):
    try:
        # get the system channel (default welcome channel)
        ch = mem.guild.system_channel
        if ch is not None:
            # send a welcome message
            await ch.send(f'Welcome, {mem.mention}!')
    except Exception as e:
        # log any errors
        print(f"Error in on_member_join: {e}")

# WORKS
# Command: Join the voice channel the user is in
@bot.command(name="join")
async def join(ctx):
    try:
        # check if the user is in a voice channel
        if ctx.author.voice:
            # get the voice channel and connect to it
            ch = ctx.author.voice.channel
            await ch.connect()
        else:
            # notify the user if they are not in a voice channel
            await ctx.send("You are not in a voice channel.")
    except Exception as e:
        # log any errors
        print(f"Error in join: {e}")

# WORKS
# Command: Leave the current voice channel
@bot.command(name="leave")
async def leave(ctx):
    try:
        # check if the bot is in a voice channel
        if ctx.voice_client:
            # disconnect from the voice channel
            await ctx.voice_client.disconnect()
        else:
            # notify the user if the bot is not in a voice channel
            await ctx.send("I am not in a voice channel.")
    except Exception as e:
        # log any errors
        print(f"Error in leave: {e}")

''' #There seems to be a ytdl error but probably on my end idk
# Command: Play a YouTube video in the voice channel
@bot.command(name="play")
async def play(ctx, url):
    try:
        # get the voice client
        vc = ctx.voice_client
        # if not in a voice channel, join the user's channel
        if not vc:
            await ctx.invoke(join)
            vc = ctx.voice_client

        # extract video information
        data = ytdl.extract_info(url, download=False)
        fn = data['url']  # Get the audio URL
        src = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(fn))  # Create audio source

        # function to handle playback completion
        def after(err):
            if err:
                print(f'Player error: {err}')
            else:
                # remove the played song from the queue
                if ctx.guild.id in que and que[ctx.guild.id]:
                    del que[ctx.guild.id][0]
                    # play the next song if available
                    if que[ctx.guild.id]:
                        asyncio.run_coroutine_threadsafe(play_next(ctx), bot.loop)

        # play the audio
        vc.play(src, after=after)
        # Add the song to the queue
        if ctx.guild.id not in que:
            que[ctx.guild.id] = []
        que[ctx.guild.id].append(url)
        # notify the user of the currently playing song
        await ctx.send(f'Now playing: {data["title"]}')

    except Exception as e:
        # notify the user of errors
        await ctx.send(f"Error: {e}")
        # log any errors
        print(f"Error in play: {e}")

# Function: Play the next song in the queue
async def play_next(ctx):
    try:
        # check if there are more songs in the queue
        if ctx.guild.id in que and len(que[ctx.guild.id]) > 1:
            next_url = que[ctx.guild.id][0]  # Get the next song
            await play(ctx, next_url)  # Play the next song
    except Exception as e:
        # log any errors
        print(f"Error in play_next: {e}")

# Command: Display the current music queue
@bot.command(name="queue")
async def queue(ctx):
    try:
        # check if there are songs in the queue
        if ctx.guild.id in que and que[ctx.guild.id]:
            q_list = "\n".join(que[ctx.guild.id])  # Format the queue as a string
            await ctx.send(f"Current Queue:\n{q_list}")  # Send the queue to the channel
        else:
            # notify the user if the queue is empty
            await ctx.send("Queue is empty.")
    except Exception as e:
        # log any errors
        print(f"Error in queue: {e}")

# Command: Skip the currently playing song
@bot.command(name="skip")
async def skip(ctx):
    try:
        # check if the bot is playing audio
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.stop()  # Stop the current song
            await ctx.send("Skipped the current song.")  # Notify the user
        else:
            # notify the user if nothing is playing
            await ctx.send("Nothing to skip.")
    except Exception as e:
        # log any errors
        print(f"Error in skip: {e}")
'''
# run the bot using the Discord token
bot.run(TOK)