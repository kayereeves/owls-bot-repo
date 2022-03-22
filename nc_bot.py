import random
import discord
import os
from discord.ext import commands
from discord_slash import SlashCommand, SlashContext
from discord_slash.utils.manage_commands import create_option
from dotenv import load_dotenv
load_dotenv('.env')

from nc_bot_sql import *

tok = os.getenv('DISCORD_TOKEN')

bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())

slash = SlashCommand(bot, sync_commands=True)

images = [
    'https://i.imgur.com/x6nMAnJ.png']

# commands from discord message

# trade report
# takes in trading data to create entry
@slash.slash(name="tr",
             description="Submit your trades to the database.",
             options=[
               create_option(
                 name="sent",
                 description="Input a list of the items/gbcs you sent with values.",
                 option_type=3,
                 required=True
               ),
               create_option(
                 name="received",
                 description="Input a list of items/gbcs you received with values.",
                 option_type=3,
                 required=True
               ),
               create_option(
                 name="notes",
                 description="Input any notes on the transactions - was it fair, unfair? Be concise!",
                 option_type=3,
                 required=False
               ),
               create_option(
                 name="date",
                 description="Input the date of the trade in YYYY-MM-DD format, e.g. 2021-08-13 (If ignored the default is today).",
                 option_type=3,
                 required=False
               )
             ],
             guild_ids=[])
                
@bot.command()
async def tr(ctx, sent: str, received: str, notes: str=None, date: str=None):
    if date:
        embed_date = f"`{date}`"
    else:
        embed_date = '`Today`'
    if notes:
        embed_notes = f"\n*** notes: {notes}"
    else:
        embed_notes = ''
    send_message = discord.Embed (
    title = 'Is this correct?',
    description = f"{embed_date}\n```diff\n~ s: {sent}\n~ r: {received }{embed_notes}\n*** reported by: {ctx.author}```",
    color = 0xffc000   
    )               
    send_message.set_thumbnail(url=random.choice(images))
    send_message.set_footer(text="Make sure you have included values where possible!")

    confirmation = await ctx.send(embed=send_message)
    await confirmation.add_reaction('👍')
    await confirmation.add_reaction('👎')
    def check(reaction, user):
            return user == ctx.author
    reaction, user = await bot.wait_for("reaction_add", timeout=60.0, check=check)
    confirmation_id = confirmation.id
    if reaction.emoji == '👍' and reaction.message.id == confirmation_id:
        result = add_trade(str(ctx.author), sent, received, date, notes)
        if not result:
            failed_message = discord.Embed (
            title = 'Trade report failed!',
            description = '```diff\n- Something went wrong, please try again! -```',
            color = 0xa52d2f   
            )                 
            failed_message.set_thumbnail(url=random.choice(images))
            failed_message.set_footer(text="Remember to format the date as YYYY-MM-DD and to avoid using single or double quotation characters!")
            await confirmation.edit(embed=failed_message)
            await confirmation.clear_reactions()
        else:
            #user_stats = return_stats(ctx)
            success_message = discord.Embed (
            title = 'Trade reported successfully!',
            #description = '```xl\nYou have now reported ' + str(user_stats) + ' trades.```',
            description = '```xl\nThe Owls thank you! 🦉```',
            color = 0x789900   
            )                 
            success_message.set_thumbnail(url=random.choice(images))
            await confirmation.edit(embed=success_message)
            await confirmation.clear_reactions()
    if reaction.emoji == '👎' and reaction.message.id == confirmation_id:
        discard_message = discord.Embed (
        title = 'Trade report discarded successfully!',
        description = '```Alright, I have set that report on a course for the nearest blackhole. Please try again!```',
        color = 0xa52d2f   
        )                 
        discard_message.set_thumbnail(url=random.choice(images))
        await confirmation.edit(embed=discard_message)
        await confirmation.clear_reactions()

# trade history
# returns the 20 most recent trade data of query
@slash.slash(name="th",
            description="View the 20 most recent reports for a particular item.",
            options=[
            create_option(
                name="query",
                description="The item you wish to view reports for.",
                option_type=3,
                required=True
            )
            ],
            guild_ids=[])
            
@bot.command()
async def th(ctx, query):
    trade_results = return_trades(query)
    if trade_results != False:
        # trade_results[0] is the total results found, trade_results[1] is the embed title, trade_results[2] are the constructed pages
        if trade_results[0] > 0:
            i = 0
            page = discord.Embed (
                title = trade_results[1],
                description = trade_results[2][0],
                color = 0x789900
    )
        page.set_thumbnail(url=random.choice(images))
        if trade_results[0] < 5:
            page.set_footer(text="Submitting trade reports or searching the database is easy! Just type / to use the commands!")
        else:
            page.set_footer(text="Submitting trade reports or searching the database is easy! Just type / to use the commands!\nPage 1")
        pages = [page]
        try:
            while i < 5:
                i += 1
                page = discord.Embed (
                    title = trade_results[1],
                    description = trade_results[2][i],
                    color = 0x789900   
                )               
                page.set_thumbnail(url=random.choice(images))
                page.set_footer(text="Submitting trade reports or searching the database is easy! Just type / to use the commands!\nPage " + str(i + 1))
                pages.append(page) 
        except IndexError:
            print('womp')
        max_i = i - 1 # max_i is the maximum index value available for trade_results[2][i]
        message = await ctx.send(embed = pages[0])
        if trade_results[0] > 4:
            await message.add_reaction('⏮')
            await message.add_reaction('◀')
            await message.add_reaction('▶')
            await message.add_reaction('⏭')
            await message.add_reaction('⏹️')

            def check(reaction, user):
                return user == ctx.author

            i = 0
            reaction = None
            message_id = message.id

            while True:
                if str(reaction) == '⏮' and reaction.message.id == message_id:
                    i = 0
                    await message.edit(embed = pages[i])
                elif str(reaction) == '◀' and reaction.message.id == message_id:
                    if i > 0:
                        i -= 1
                        await message.edit(embed = pages[i])
                elif str(reaction) == '▶' and reaction.message.id == message_id:
                    if i < max_i:
                        i += 1
                        await message.edit(embed = pages[i])
                elif str(reaction) == '⏭' and reaction.message.id == message_id:
                    i = max_i
                    await message.edit(embed = pages[i])
                elif str(reaction) == '⏹️' and reaction.message.id == message_id:
                    await message.clear_reactions()
                
                try:
                    reaction, user = await bot.wait_for('reaction_add', timeout = 30.0, check = check)
                    await message.remove_reaction(reaction, user)
                except:
                    break
            await message.clear_reactions()
    else:
        womp = discord.Embed (
            description = '```diff\n-         Error Code: 34323948293423490         -\nAbsolutely no results could be found. Nada. Zero.\n-         Error Code: 34323948293423490         -```',
            color = 0xa52d2f
        )
        womp.set_thumbnail(url=random.choice(images))
        womp.set_footer(text="Submitting trade reports or searching the database is easy! Just type / to use the commands!")
        message = await ctx.send(embed = womp)

# returns the 40 most recent trade reports
@slash.slash(name="logs",
            description="View the 40 most recent trade reports.",
            guild_ids=[])
            
@bot.command()
async def logs(ctx):
    trade_results = recent_trades(ctx)
    if trade_results != False:
        # trade_results[0] is the total results found, trade_results[1] is the embed title, trade_results[2] are the constructed pages
        if trade_results[0] > 0:
            i = 0
            page = discord.Embed (
                title = trade_results[1],
                description = trade_results[2][0],
                color = 0x789900
    )
        page.set_thumbnail(url=random.choice(images))
        if trade_results[0] < 5:
            page.set_footer(text="Submitting trade reports or searching the database is easy! Just type / to use the commands!")
        else:
            page.set_footer(text="Submitting trade reports or searching the database is easy! Just type / to use the commands!\nPage 1")
        pages = [page]
        try:
            while i < 10:
                i += 1
                page = discord.Embed (
                    title = trade_results[1],
                    description = trade_results[2][i],
                    color = 0x789900   
                )               
                page.set_thumbnail(url=random.choice(images))
                page.set_footer(text="Submitting trade reports or searching the database is easy! Just type / to use the commands!\nPage " + str(i + 1))
                pages.append(page) 
        except IndexError:
            print('womp')
        max_i = i - 1 # max_i is the maximum index value available for trade_results[2][i]
        message = await ctx.send(embed = pages[0])
        if trade_results[0] > 4:
            await message.add_reaction('⏮')
            await message.add_reaction('◀')
            await message.add_reaction('▶')
            await message.add_reaction('⏭')
            await message.add_reaction('⏹️')

            def check(reaction, user):
                return user == ctx.author

            i = 0
            reaction = None
            message_id = message.id

            while True:
                if str(reaction) == '⏮' and reaction.message.id == message_id:
                    i = 0
                    await message.edit(embed = pages[i])
                elif str(reaction) == '◀' and reaction.message.id == message_id:
                    if i > 0:
                        i -= 1
                        await message.edit(embed = pages[i])
                elif str(reaction) == '▶' and reaction.message.id == message_id:
                    if i < max_i:
                        i += 1
                        await message.edit(embed = pages[i])
                elif str(reaction) == '⏭' and reaction.message.id == message_id:
                    i = max_i
                    await message.edit(embed = pages[i])
                elif str(reaction) == '⏹️' and reaction.message.id == message_id:
                    await message.clear_reactions()
                
                try:
                    reaction, user = await bot.wait_for('reaction_add', timeout = 30.0, check = check)
                    await message.remove_reaction(reaction, user)
                except:
                    break
            await message.clear_reactions()
    else:
        womp = discord.Embed (
            description = '```diff\n-         Error Code: 34323948293423490         -\nAbsolutely no results could be found. Nada. Zero.\n-         Error Code: 34323948293423490         -```',
            color = 0xa52d2f
        )
        womp.set_thumbnail(url=random.choice(images))
        womp.set_footer(text="Submitting trade reports or searching the database is easy! Just type / to use the commands!")
        message = await ctx.send(embed = womp)

# prints help for use of bot
@slash.slash(name="help",
            description="View command info for Report-A-Trade Bot.",
            guild_ids=[])
            
@bot.command()
async def bothelp(ctx):
    bothelp = discord.Embed (
        title = 'Help',
        description = 
        """This bot helps record and display NC trade report data submitted by the community.
        Type `/` followed by a command (or find the command in the slash commands menu) to interact with the bot.

        \n\n
        **/tr**\n
        ```\n Submit a trade report. You will be prompted to input what you sent and what you received.\n\n
        You may also choose to add a note to your report as well as record the date in YYYY-MM-DD format
        (if you do not input a date, the current date will be used).\n

        ```\n**/th**\n```
        \nSearch the database. You will be prompted to input the item which you wish to view trade reports for.\n

        ```\n**/logs**\n
        ```\nView the 40 most recent reported trades.\n```""",
        color = 0xE5D8D9
    )
    bothelp.set_thumbnail(url=random.choice(images))
                    
    await ctx.send(embed=bothelp)

# creates a download file of recently reported trading data
@bot.command()
async def download(ctx, date):
    if (str(ctx.author) in ('imgonnageta#1995', 'Kaye#1200')):
        result = return_file(date)
        file_path = "download.csv"
        if result:
            await ctx.send(file=discord.File(file_path))

bot.run(tok)
