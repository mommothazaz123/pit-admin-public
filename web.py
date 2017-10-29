'''
Created on Jan 13, 2017

@author: Andrew Zhu, Team 2144
'''

import asyncio
import datetime
import os

from aiohttp import web
import discord
from discord.ext import commands
import pytz
import aiohttp


TEAM_NUM = '2144'
TIME_ZONE = 'US/Pacific'

class Web:
    """A TBA Webhook handler.
    Built to be plug & play to a discord.py discord bot."""
    
    COMP_LEVELS_VERBOSE = {
        "qm": "Quals",
        "ef": "Eighths",
        "qf": "Quarters",
        "sf": "Semis",
        "f": "Finals",
    }
    
    def __init__(self, bot):
        self.bot = bot
        self.following_channels = self.bot.db.not_json_get("tba-follow", [])
        loop = self.bot.loop
        app = web.Application(loop=loop)
        app.router.add_post('/tba-hook', self.tba_handler)
        self.run_app(app, host=os.environ.get('HOST'), port=os.environ.get('PORT'))
        
    @commands.command(pass_context=True, no_pm=True)
    async def sub(self, ctx):
        """Subs to TBA hook notifications."""
        if not ctx.message.channel.id in self.following_channels:
            self.following_channels.append(ctx.message.channel.id)
            await self.bot.say("Subbed.")
        else:
            self.following_channels.remove(ctx.message.channel.id)
            await self.bot.say("Unsubbed.")
        self.bot.db.not_json_set("tba-follow", self.following_channels)
        
    @commands.command(no_pm=True)
    async def test_update(self):
        async with aiohttp.ClientSession(headers={"X-TBA-App-Id":"frc2144:discord_bot:1"}) as client:
            async with client.request('GET', 'https://www.thebluealliance.com/api/v2/event/2017nvlv/rankings') as r:
                if r.status == 200:
                    js = await r.json()
                    headers = js[0]
                    teams = js[1:]
                    team_data = []
                    for team in teams:
                        out = {}
                        for field in range(len(team)):
                            out[headers[field]] = team[field]
                        team_data.append(out)
                    print(team_data)
                    us = next(team for team in team_data if str(team.get('Team')) == TEAM_NUM)
                    rank = us.get('Rank')
                    wlt = us.get('Record (W-L-T)')
                    stats = "Rank {}, {} W-L-T".format(rank, wlt)
                    await self.bot.change_presence(game=discord.Game(name=stats))
            
    async def tba_handler(self, request):
        data = await request.json()
        print("Accepted request:\n{}".format(data))
        outData = self.parse_tba_data(data)
        for c in self.following_channels:
            channel = discord.Object(id=c)
            if outData.get('type', 'Text') == 'Embed':
                await self.bot.send_message(channel, embed=outData['embed'])
            else:
                if outData['text'] is not '':
                    await self.bot.send_message(channel, outData['text'])
                else:
                    await self.bot.send_message(channel, "Unhandled event from TBA!: \n{}".format(outData['data']))
        async with aiohttp.ClientSession(headers={"X-TBA-App-Id":"frc2144:discord_bot:1"}) as client:
            async with client.request('GET', 'https://www.thebluealliance.com/api/v2/event/2017nvlv/rankings') as r:
                if r.status == 200:
                    js = await r.json()
                    headers = js[0]
                    teams = js[1:]
                    team_data = []
                    for team in teams:
                        out = {}
                        for field in range(len(team)):
                            out[headers[field]] = team[field]
                        team_data.append(out)
                    us = next(team for team in team_data if str(team.get('Team')) == TEAM_NUM)
                    rank = us.get('Rank')
                    wlt = us.get('Record (W-L-T)')
                    rp = us.get('Ranking Score')
                    stats = "Rank {}, {} W-L-T, {} RP.".format(rank, wlt, rp)
                    await self.bot.change_presence(game=discord.Game(name=stats))
        return web.Response()
    
    def parse_tba_data(self, data):
        out = {'data': data, 'type': 'Text'}
        
        message_type = data['message_type']
        message_data = data['message_data']
        
        embed = discord.Embed()
        embed.set_footer(text='Event recieved at')
        embed.timestamp = datetime.datetime.now()
        
        text = ""
        
        if message_type == 'ping':
            out['type'] = 'Embed'
            embed.colour = 0xff00d4  # pink!
            embed.title = message_data['title']
            embed.description = message_data['desc']
            
        if message_type == 'upcoming_match':
            out['type'] = 'Embed'
            embed.colour = 0xc7ff00  # yellow-green
            embed.title = "Upcoming Match"
            embed.url = "https://www.thebluealliance.com/match/" + message_data.get('match_key')
            embed.description = "Match Upcoming in {} - {}!".format(message_data.get('event_name'), message_data.get('match_key'))
            embed.add_field(name="Estimated Starting Time", value=datetime.datetime.fromtimestamp(message_data.get('predicted_time', 0), tz=pytz.timezone(TIME_ZONE)).strftime('%I:%M %p'))
            embed.add_field(name="Scheduled Starting Time", value=datetime.datetime.fromtimestamp(message_data.get('scheduled_time', 0), tz=pytz.timezone(TIME_ZONE)).strftime('%I:%M %p'))
            team_keys = message_data.get('team_keys', [])
            red = team_keys[int(len(team_keys) / 2):]
            blue = team_keys[:int(len(team_keys) / 2)]
            embed.add_field(name="Red Alliance", value='\n'.join(red).replace('frc', '').replace(TEAM_NUM, "**" + TEAM_NUM + "**"))
            embed.add_field(name="Blue Alliance", value='\n'.join(blue).replace('frc', '').replace(TEAM_NUM, "**" + TEAM_NUM + "**"))
            if 'frc' + TEAM_NUM in red: embed.colour = 0xff0000  # red
            if 'frc' + TEAM_NUM in blue: embed.colour = 0x0000ff  # blue
            
        if message_type == 'match_score':
            out['type'] = 'Embed'
            embed.colour = 0xffff00  # green
            embed.title = "Match Scores"
            match = message_data.get('match', {})
            embed.url = "https://www.thebluealliance.com/match/" + match.get('key')
            red = match.get('alliances').get('red')
            blue = match.get('alliances').get('blue')
            embed.add_field(name="Red Alliance - " + str(red.get('score')), value='\n'.join(red.get('teams')).replace('frc', '').replace(TEAM_NUM, "**" + TEAM_NUM + "**"))
            embed.add_field(name="Blue Alliance - " + str(blue.get('score')), value='\n'.join(blue.get('teams')).replace('frc', '').replace(TEAM_NUM, "**" + TEAM_NUM + "**"))
            if red.get('score') == blue.get('score'):
                victoryString = "Tie"
            elif red.get('score') > blue.get('score'):
                victoryString = "Red Wins"
                embed.colour = 0xff0000  # red
            else:
                victoryString = "Blue Wins"
                embed.colour = 0x0000ff  # blue
            embed.description = "Match Results for {} - {}!".format(match.get('key'), victoryString)
            self.bot.db.set('last_match', str(match.get('match_number', 0)))
            
        if message_type == 'starting_comp_level':
            out['type'] = 'Embed'
            embed.colour = 0x4b00bc  # blurple
            embed.title = "Starting Match Level"
            event_name = message_data.get('event_name', 'Unknown Event')
            comp_level = message_data.get('comp_level', '')
            comp_level = self.COMP_LEVELS_VERBOSE.get(comp_level, 'Unknown Level')
            starting_time = datetime.datetime.fromtimestamp(message_data.get('scheduled_time', 0), tz=pytz.timezone(TIME_ZONE)).strftime('%I:%M %p')
            embed.description = "{} starting at {}!\nEstimated starting time: {}".format(comp_level, event_name,
                                                                                         starting_time)
            
        if message_type == 'alliance_selection':
            out['type'] = 'Embed'
            embed.colour = 0x008962  # dark cyan
            embed.title = "Alliance Selection"
            event = message_data.get('event', {})
            event_name = event.get('name', 'Unknown Event')
            alliances = event.get('alliances', [])
            embed.description = "Alliances have been selected at {}!".format(event_name)
            for num, a in enumerate(alliances):
                embed.add_field(name='Alliance {}'.format(num + 1), value='\n'.join(a.get('picks')).replace('frc', '').replace(TEAM_NUM, "**" + TEAM_NUM + "**"))
             
        if message_type == 'schedule_updated':
            out['type'] = 'Embed'
            embed.colour = 0x4b00bc  # blurple
            embed.title = "Schedule Updated"
            event_name = message_data.get('event_name', 'Unknown Event')
            first_match_time = datetime.datetime.fromtimestamp(message_data.get('first_match_time', 0), tz=pytz.timezone(TIME_ZONE)).strftime('%I:%M %p')
            embed.description = "Schedule updated at {}!\nEstimated starting time: {}".format(event_name,
                                                                                         first_match_time)
                
        if message_type == 'broadcast':
            out['type'] = 'Embed'
            embed.colour = 0xff00d4  # pink!
            embed.title = message_data['title']
            embed.description = message_data['desc']
            embed.url = message_data.get('url')
                        
        out['embed'] = embed
        out['text'] = text
        return out

    def run_app(self, app, *, host='0.0.0.0', port=None,
            shutdown_timeout=60.0, ssl_context=None,
            print=print, backlog=128):
        """Run an app"""
        if port is None:
            if not ssl_context:
                port = 8080
            else:
                port = 8443
    
        loop = app.loop
    
        handler = app.make_handler()
        server = loop.create_server(handler, host, port, ssl=ssl_context,
                                    backlog=backlog)
        srv, startup_res = loop.run_until_complete(asyncio.gather(server,
                                                                  app.startup(),
                                                                  loop=loop))
    
        scheme = 'https' if ssl_context else 'http'
        print("======== Running on {scheme}://{host}:{port}/ ========\n"
              "(Press CTRL+C to quit)".format(
                  scheme=scheme, host=host, port=port))
