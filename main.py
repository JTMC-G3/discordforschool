import asyncio
import threading
from flask import Flask, render_template, request, redirect, url_for, flash
import discord
from dotenv import load_dotenv
import os
import json
import logging




client = discord.Client()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "fallback_key")
DISCORD_USER_TOKEN = os.getenv("DISCORD_USER_TOKEN")

app = Flask(__name__)
app.secret_key = SECRET_KEY

def run_client():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(client.start(DISCORD_USER_TOKEN))

client_thread = threading.Thread(target=run_client, daemon=True)
client_thread.start()

guild_channels = {}  

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")
    for guild in client.guilds:
        print(guild.name)
        guild_channels[guild.name] = []
        for channel in guild.channels:
            if isinstance(channel, discord.TextChannel):  
                guild_channels[guild.name].append((channel.name, channel.id))






@app.route("/messages/<int:channel_id>", methods=["GET"])
def get_messages(channel_id):
    before_id = request.args.get("before")
    after_id = request.args.get("after")

    async def _fetch():
        channel = await client.fetch_channel(channel_id)
        kwargs = {"limit": 10}
        if before_id:
            kwargs["before"] = discord.Object(id=int(before_id))
        if after_id:
            kwargs["after"] = discord.Object(id=int(after_id))

        messages = []
        async for msg in channel.history(**kwargs):
            messages.append({
                "id": str(msg.id),                 # stringify
                "author": str(msg.author),
                "author_id": str(msg.author.id),   # stringify
                "content": msg.content,
                "created_at": msg.created_at.strftime("%Y-%m-%d %H:%M:%S")
            })


        return messages

    future = asyncio.run_coroutine_threadsafe(_fetch(), client.loop)
    try:
        messages = future.result()
    except Exception as e:
        return {"error": str(e)}, 500

    return {"messages": messages}


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html", guild_channels=guild_channels)

@app.route("/send", methods=["POST"])
def send():
    channel_id = request.form.get("channel_id", "").strip()
    message = request.form.get("message", "").strip()

    if not channel_id or not message:
        return {"error": "Channel ID and message are required."}, 400

    try:
        cid_int = int(channel_id)
    except ValueError:
        return {"error": "Channel ID must be a number."}, 400

    async def _send():
        channel = await client.fetch_channel(cid_int)
        msg = await channel.send(message)
        return {
            "id": str(msg.id),                 # stringify
            "author": str(msg.author),
            "author_id": str(msg.author.id),   # stringify
            "content": msg.content,
            "created_at": msg.created_at.strftime("%Y-%m-%d %H:%M:%S")
        }



    future = asyncio.run_coroutine_threadsafe(_send(), client.loop)
    try:
        sent_message = future.result()
        return {"message": sent_message}, 200
    except Exception as e:
        return {"error": str(e)}, 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)



print("hi")



