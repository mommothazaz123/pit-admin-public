'''
Created on Oct 20, 2016

@author: andrew
'''

import asyncio
from ssl import Purpose
import ssl
from urllib.request import Request, urlopen

import aiohttp
import discord
from discord.ext import commands

import checks
from functions import format_table
import time
import datetime
import pytz


class PitUtils:
    '''
    Utilities for competition pit crew.
    '''

    def __init__(self, bot):
        self.bot = bot
        self.pinging = []
        self.last_match = self.bot.db.get('last_match', '0')
        self.comp = self.bot.db.get('current_comp', '')
        
    async def on_message(self, message):
        if message.author in self.pinging:
            self.pinging.remove(message.author)
            
        
    @commands.command()
    @checks.mod_or_permissions(kick_members=True)
    async def ping(self, target : discord.User, *, message = None):
        """Pings someone. Kinda annoying."""
        self.pinging.append(target)
        await self.bot.send_message(target, "You've been pinged! Say anything to stop.")
        for i in range(100):
            msg = message if message is not None else "PING!"
            if target in self.pinging:
                await self.bot.send_message(target, msg)
                await asyncio.sleep(3)
            else:
                await self.bot.send_message(target, "Acknowledgement recieved.")
                await self.bot.say(target.mention + " has acknowledged the ping.")
                return
        await self.bot.say(target.mention + "'s ping timed out.")
        
    @commands.command(pass_context=True, name='comp')
    async def compSet(self, ctx, comp : str):
        """Sets the current competition for default getting."""
        self.comp = comp
        self.bot.db.set('current_comp', comp)
        await self.bot.edit_channel(ctx.message.server.default_channel, topic = "Current Comp: " + comp)
        await self.bot.say("Comp updated.")
    
    @commands.command(name='next')
    async def nextMatch(self, comp : str=None):
        """Grabs the next match from a competition that we're in."""
        if comp is None: comp = self.comp
        self.last_match = self.bot.db.get('last_match', '0')
        async with aiohttp.ClientSession(headers={"X-TBA-App-Id":"frc2144:discord_bot:1"}) as client:
            async with client.request('GET', 'https://www.thebluealliance.com/api/v2/team/frc2144/event/{}/matches'.format(comp)) as r:
                if r.status == 200:
                    js = await r.json()
                    try:
                        nextMatch = next(match for match in sorted(js, key=lambda k: k['match_number'])  if match['match_number'] > int(self.last_match))
                    except StopIteration:
                        return await self.bot.say("No matches found.")
                    embed = discord.Embed(title=str(nextMatch.get('key', "Unknown Match")) + " ({})".format(nextMatch.get('time_string', None) or datetime.datetime.fromtimestamp(nextMatch.get('time',0), tz=pytz.timezone('US/Pacific')).strftime('%I:%M %p')))
                    embed.add_field(name='Blue Alliance', value=(",\n".join(nextMatch.get('alliances', {}).get('blue', {}).get('teams', []))).replace('frc2144', '**frc2144**'))
                    embed.add_field(name='Red Alliance', value=(",\n".join(nextMatch.get('alliances', {}).get('red', {}).get('teams', []))).replace('frc2144', '**frc2144**'))
                    await self.bot.say(embed=embed)
                    
    @commands.command()
    async def match(self, match:str):
        """Grabs a match from a competition that we're in."""
        async with aiohttp.ClientSession(headers={"X-TBA-App-Id":"frc2144:discord_bot:1"}) as client:
            async with client.request('GET', 'https://www.thebluealliance.com/api/v2/match/{}'.format(match)) as r:
                if r.status == 200:
                    nextMatch = await r.json()
                    embed = discord.Embed(title=str(nextMatch.get('key', "Unknown Match")) + " ({})".format(nextMatch.get('time_string', None) or datetime.datetime.fromtimestamp(nextMatch.get('time',0)).strftime('%H:%M %p')))
                    embed.add_field(name='Blue Alliance', value=("\n".join(nextMatch.get('alliances', {}).get('blue', {}).get('teams', []))).replace('frc2144', '**frc2144**'))
                    embed.add_field(name='Red Alliance', value=("\n".join(nextMatch.get('alliances', {}).get('red', {}).get('teams', []))).replace('frc2144', '**frc2144**'))
                    await self.bot.say(embed=embed)
                    
    @commands.command()
    async def ranks(self, comp : str=None):
        """Grabs the ranks (top 10) from a competition."""
        if comp is None: comp = self.comp
        async with aiohttp.ClientSession(headers={"X-TBA-App-Id":"frc2144:discord_bot:1"}) as client:
            async with client.request('GET', 'https://www.thebluealliance.com/api/v2/event/{}/rankings'.format(comp)) as r:
                if r.status == 200:
                    js = await r.json()
                    js = js[:11]
                    data = format_table(js)
                    await self.bot.say("```\n"+data+"```")
        
        