from flask import Flask, request, redirect
import discord
from discord.ext import commands
import requests
import asyncio
import json

# url: https://discord.com/api/oauth2/authorize?client_id=950551806210097182&permissions=8&redirect_uri=http%3A%2F%2F127.0.0.1%3A5000%2Fauth%2Fcallback&response_type=code&scope=identify%20guilds.join%20bot

bot = commands.Bot(command_prefix="$", intents=discord.Intents.all())
app = Flask(__name__)

with open("./settings.json") as file:
    credentials = json.load(file)

bot_token = credentials['bot_token']
client_secret =  credentials['client_secret']
guild_id = credentials['guild_id']
category_id = credentials['category_id']


def add_user_to_server(token: str, user_id: str, server_id: str, access_token: str) -> bool:
    url = f'https://discordapp.com/api/v8/guilds/{server_id}/members/{user_id}'
    headers = {
        'Authorization': f'Bot {token}'
    }

    data = {
        "access_token": access_token
    }

    response = requests.put(url, headers=headers, json=data)
    if response.status_code == 201:
        print(f'User {user_id} added to server with ID {server_id}')
        return True
    else:
        print(f'Error adding user {user_id} to server with ID {server_id}')
        return False

async def create_channel(channel_name:str):
    guild:discord.Guild = await bot.get_guild(guild_id)
    category = discord.utils.get(guild.categories, id=category_id)
    channel = await guild.create_text_channel(name=channel_name, category=category)
    invite = await channel.create_invite(reason="User authorized on Flask Application")
    return invite.url



# The callback URL for OAuth2 authorization
@app.route('/auth/callback')
def callback():
    code = request.args.get('code')

    # Exchange the authorization code for an access token
    url = 'https://discord.com/api/oauth2/token'
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    data = {
        'client_id': '1101425504642404352',
        'client_secret': client_secret,
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': 'http://127.0.0.1:5000/auth/callback',
        'scope': 'identify guilds.join'
    }
    response = requests.post(url, headers=headers, data=data).json()
    access_token = response['access_token']

    # Get the user ID from the access token
    url = 'https://discord.com/api/users/@me'
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    response = requests.get(url, headers=headers).json()
    user_id = response['id']

    # Add the user to the server
    invite_code = guild_id
    add_user_to_server(bot_token, user_id, invite_code, access_token)
    invite = create_channel(channel_name=user_id)

    return redirect(location=invite, code=302)

if __name__ == '__main__':
    app.run(debug=True)
    bot.run(bot_token)
