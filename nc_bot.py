import random
import discord
import os
import interactions
import secret
from interactions import ActionRow, ComponentContext
import os.path
from discord.ext import commands
from dotenv import load_dotenv
import gc
load_dotenv('.env')
from nc_bot_sql import *
import random
import string

#tok = os.getenv('DISCORD_TOKEN')
tok = secret.tok
bot = interactions.Client(tok)

images = [
    'https://i.imgur.com/x6nMAnJ.png']

custom_ids = []

class my_button(interactions.Button):
    def __init__(self, *args, **kwargs):
        super(my_button, self).__init__(*args, **kwargs)
        self.user = kwargs.pop('user')
        self.sent = kwargs.pop('sent')
        self.received = kwargs.pop('received')
        self.notes = kwargs.pop('notes')
        self.date = kwargs.pop('date')

# commands from discord message

buttons = [
        interactions.Button(
        style=interactions.ButtonStyle.PRIMARY,
        label="👍",
        custom_id="thumbsup"),
        interactions.Button(
        style=interactions.ButtonStyle.PRIMARY,
        label="👎",
        custom_id="thumbsdown")
]

@bot.component("thumbsup")
async def button_response(ctx: interactions.ComponentContext):
    #send the data to the database
    result = add_trade(b.user, b.sent, b.received, b.date, b.notes)
 
    if not result:
        failed_message = interactions.Embed (
        title = 'Trade report failed!',
        description = '```diff\n- Something went wrong, please try again! -```',
        color = 0x654321  
        )                 
        failed_message.set_thumbnail(url=random.choice(images))
        failed_message.set_footer(text="Remember to format the date as YYYY-MM-DD!")
        await confirmation.edit(embeds=failed_message)
    else:
        success_message = interactions.Embed (
        title = 'Trade reported successfully!',
        description = '```xl\nThe Owls thank you! 🦉```',
        color = 0x654321   
        )                 
        success_message.set_thumbnail(url=random.choice(images))
 
    try:
        await ctx.disable_all_components()
    except Exception as e:
        print(e)
 
    await ctx.message.edit(embeds=success_message, components=[])

@bot.component("thumbsdown")
async def button_response(ctx: interactions.ComponentContext):
    discard_message = interactions.Embed (
    title = 'Trade report discarded successfully!',
    description = '```Alright, I have set that report on a course for the nearest birds nest to be recycled for nesting material. Please try again!```',
    color = 0x654321   
    )                 
    discard_message.set_thumbnail(url=random.choice(images))
    try:
        await ctx.disable_all_components()
    except Exception as e:
        print(e)
            
    await ctx.message.edit(embeds=discard_message, components=None)

# trade history
# returns the 20 most recent trade data of query
@bot.command(name="search",
            description="View the 8 most recent reports for a particular item.",
            options=[
            interactions.Option(
                name="query",
                description="The item you wish to view reports for.",
                type=interactions.OptionType.STRING,
                required=True
            )
            ],
)
            
async def search(ctx: interactions.CommandContext, query):
    trade_results = return_trades(query)
    if trade_results != False:
        # trade_results[0] is the total results found, trade_results[1] is the embed title, trade_results[2] are the constructed pages
        if trade_results[0] > 0:
            page = interactions.Embed (
                title = trade_results[1],
                description = trade_results[2][0],
                color = 0x654321
    )
        page.set_thumbnail(url=random.choice(images))
        if trade_results[0] < 6:
            page.set_footer(text="Submitting trade reports or searching the database is easy! Just type / to use the commands!")
        else:
            page.set_footer(text="Submitting trade reports or searching the database is easy! Just type / to use the commands!")
        pages = [page]

        try:
            i = 0
            while i < 8:
                page = interactions.Embed (
                    title = trade_results[1],
                    description = trade_results[2][i],
                    color = 0x654321   
                )
                i += 1        
                page.set_thumbnail(url=random.choice(images))
                page.set_footer(text="Submitting trade reports or searching the database is easy! Just type / to use the commands!")
                pages.append(page) 
        except IndexError:
            print('womp')
        
        message = await ctx.send(embeds = pages[0])

    else:
        womp = interactions.Embed (
            description = '```diff\n-         Error Code: 34323948293423490         -\nAbsolutely no results could be found. Nada. Zero.\n-         Error Code: 34323948293423490         -```',
            color = 0x654321
        )
        womp.set_thumbnail(url=random.choice(images))
        womp.set_footer(text="Submitting trade reports or searching the database is easy! Just type / to use the commands!")
        message = await ctx.send(embeds = womp)

#help command
@bot.command(
    name="owl",
    description = "View a list of commands."
)

async def owl(ctx: interactions.CommandContext):
    owl = interactions.Embed (
        title = 'OwlBot 2.0 Help',
        description = 
        """This bot helps record and display NC trade report data submitted by the community. Type `/` followed by a command to interact with the bot.

        **/report**
        ```\nSubmit a trade report. You will be prompted to input what you sent and what you received.\n\nYou may also choose to add a note to your report as well as record the date in YYYY-MM-DD format (if you do not input a date, the current date will be used).```
        **/search**
        ```\nSearch the database. You will be prompted to input the item which you wish to view trade reports for.```
        **/credits**
        ```\nView credits for OwlBot 2.0.```""",
        color = 0x654321
    )
    owl.set_thumbnail(url=random.choice(images))
                    
    await ctx.send(embeds=owl)

#credits command            
@bot.command(
    name="credits",
    description="View credits for OwlBot 2.0."
)            

async def owlcredits(ctx: interactions.CommandContext):
    owlcredits = interactions.Embed (
        title = 'OwlBot Credits!',
        description = 
        """**🦉 Maya and Rawbee**
        ```\noriginal source code```
        **🦉 Ben**
        ```\nOwls CSV parser```
        **🦉 Kaye and Mallory**
        ```\nbuilding and maintaining OwlBot 2.0```
        **🦉 The ~Owls team**
        ```\nworking tirelessly to collect, record, and count trade data```
        **🦉 YOU**
        ```\nthanks for submitting your trades to us, we couldn't do it without you ❤️```""",
        color = 0x654321
    )
    owlcredits.set_thumbnail(url=random.choice(images))
                    
    await ctx.send(embeds=owlcredits)

# trade report
# takes in trading data to create entry
@bot.command(
    name="report",
    description="Submit a trade report to OWLS."
)

async def report(ctx: interactions.CommandContext):
    modal = interactions.Modal(
        title = "Report a Neocash trade to OWLS",
        custom_id = "report",
        components = [
            interactions.TextInput(
            style=interactions.TextStyleType.PARAGRAPH,
            label="Sent (Full item names & personal values!)",
            custom_id="sent",
            placeholder="Plz follow format or report may not appear in searches! Ex.: Item (1-2) + Another Item (10) + 2 GBCs",
            min_length=1
            ),
            interactions.TextInput(
            style=interactions.TextStyleType.PARAGRAPH,
            label="Received (Full item names & personal values!)",
            custom_id="received",
            placeholder="Plz follow format or report may not appear in searches! Ex.: Item (1-2) + Another Item (10) + 2 GBCs",
            min_length=1
            ),
            interactions.TextInput(
            style=interactions.TextStyleType.PARAGRAPH,
            label="Notes",
            custom_id="notes",
            value="Fair",
            min_length=0
            ),
            interactions.TextInput(
            style=interactions.TextStyleType.SHORT,
            label="Date (YYYY-MM-DD format only please)",
            custom_id="date",
            value=datetime.now().strftime('%Y-%m-%d'),
            min_length=10,
            max_length=10,
            )
        ],
    )
    await ctx.popup(modal)

@bot.modal("report")
async def modal_response(ctx: interactions.CommandContext, sent: str, received: str, notes:str, date:str):
    #user discord tag
    user = ctx.author.user.username + "#" + ctx.author.user.discriminator
 
    #request confirmation
    send_message = interactions.Embed (
    title = 'Is this correct? Press 👍 to finish submitting your report or 👎 to discard.',
    description = f"`{date}`\n```diff\n~ s: {sent}\n~ r: {received}\n*** notes: {notes}\n*** reported by: {user}```",
    color = 0x654321   
    )               
    send_message.set_thumbnail(url=random.choice(images))
    send_message.set_footer(text="Make sure you have included values where possible and followed the correct format!")

    global b 
    b = my_button(
        style=interactions.ButtonStyle.PRIMARY,
        label="👍",
        custom_id="thumbsup",
        user=user,
        sent=sent,
        received=received,
        notes=notes,
        date=date)
 
    confirmation = await ctx.send(embeds=send_message, components=[
        b,
        buttons[1]])

bot.start()
