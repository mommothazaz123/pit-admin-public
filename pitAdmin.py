'''
Created on Oct 20, 2016

@author: andrew
'''

import asyncio

import discord
from discord.ext import commands

import adminUtils
import customCommands
from dataIO import DataIO
from functions import *
import pitUtils
import web


bot = commands.Bot(command_prefix=['//', './'], description="Pit Admin, a FRC bot.", pm_help=True)

bot.db = DataIO()

#WEB


@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')
    
@bot.event
async def on_member_join(member):
    await bot.wait_until_ready()
    await bot.send_message(member.server, "Welcome to the server " + member.mention + "!")
    
@bot.event
async def on_command_error(error, ctx):
    if isinstance(error, commands.CommandNotFound):
        print("Error: " + repr(error))
        return
    else:
        await bot.send_message(ctx.message.channel, "Error: " + str(error))
        
@bot.event
async def on_message(message):
    await bot.process_commands(message)
        
bot.add_cog(customCommands.CustomCommands(bot))
bot.add_cog(adminUtils.AdminUtils(bot))
bot.add_cog(pitUtils.PitUtils(bot))

bot.run('TOKEN')
