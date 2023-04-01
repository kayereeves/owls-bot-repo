import random
import interactions
import secret
import requests
from interactions import ActionRow, ComponentContext
from nc_bot_sql import *

tok = secret.tok
bot = interactions.Client(tok)

class my_button(interactions.Button):
    def __init__(self, *args, **kwargs):
        super(my_button, self).__init__(*args, **kwargs)
        self.user = kwargs.pop('user')
        self.sent = kwargs.pop('sent')
        self.received = kwargs.pop('received')
        self.notes = kwargs.pop('notes')
        self.date = kwargs.pop('date')

# commands from discord message
@bot.component("thumbsup")
async def button_response(ctx: interactions.ComponentContext):
    #send the data to the database
    result = add_trade(b.user, b.sent, b.received, b.date, b.notes)
 
    if not result:
        failed_message = interactions.Embed (
        title = 'Trade report failed! :(',
        description = '```diff\nSomething went wrong, please try again and remember to format the date as YYYY-MM-DD!```',
        color = 0x654321  
        )                 
        failed_message.set_thumbnail(url='https://neo-owls.net/images/bot_thumb')
        await ctx.send(embeds=failed_message, components=[], ephemeral=True)
    else:
        success_message = interactions.Embed (
        title = 'Trade reported successfully! :) You can dismiss these messages.',
        description = '```xl\nThe Owls thank you! 🦉 Please dismiss these messages.```',
        color = 0x654321   
        )                 
        success_message.set_thumbnail(url='https://neo-owls.net/images/bot_thumb')
        await ctx.send(embeds=success_message, components=[], ephemeral=True)

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
    footer = "Submitting trade reports or searching the database is easy! Just type / to use the commands!"
    if trade_results != False and trade_results[0] > 0:
        response = requests.get('https://neo-owls.net/itemdata/' + query)

        if response.status_code == 404:
            title_str = trade_results[1]
        else:
            value_data = response.json()
            if value_data['owls_value'] != '':
                title_str = trade_results[1] + "\t(~OWLS value " + value_data['owls_value'] + ")"
            else:
                title_str = trade_results[1] + "\t(no ~OWLS value)"

        # trade_results[0] is the total results found, trade_results[1] is the embed title, trade_results[2] are the constructed pages
        page = interactions.Embed (
            title = title_str,
            description = trade_results[2][0],
            color = 0x654321
        )
        page.set_thumbnail(url='https://neo-owls.net/images/bot_thumb')
        page.set_footer(text=footer)
                
        message = await ctx.send(embeds = page, ephemeral=True)

    else:
        womp = interactions.Embed (
            title=trade_results[1],
            description = '```diff\nSorry, we don\'t have any trade reports for \'' + query + '\' just yet. Please make sure you\'re searching for the full, correct item name!```',
            color = 0x654321
        )
        womp.set_thumbnail(url='https://neo-owls.net/images/bot_thumb')
        womp.set_footer(text=footer)
        await ctx.send(embeds = womp, ephemeral=True)

#help command
@bot.command(
    name="owl",
    description = "View a list of commands."
)

async def owl(ctx: interactions.CommandContext):
    owl = interactions.Embed (
        title = 'OwlBot Reloaded Help',
        description = 
        """This bot helps record and display NC trade report data submitted by the community. Type `/` followed by a command to interact with the bot.

        **/report**
        ```\nSubmit a trade report. You will be prompted to input what you sent and what you received.\n\nYou may also choose to add a note to your report as well as record the date in YYYY-MM-DD format.```
        **/search**
        ```\nSearch the database. You will be prompted to input the item which you wish to view trade reports for.```
        **/credits**
        ```\nView credits for OwlBot Reloaded.```""",
        color = 0x654321
    )
    owl.set_thumbnail(url='https://neo-owls.net/images/bot_thumb')
                    
    await ctx.send(embeds=owl, ephemeral=True)

#credits command            
@bot.command(
    name="credits",
    description="View credits for OwlBot Reloaded."
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
        ```\nbuilding and maintaining OwlBot Reloaded```
        **🦉 The ~Owls team**
        ```\nworking tirelessly to collect, record, and count trade data```
        **🦉 YOU**
        ```\nthanks for submitting your trades to us, we couldn't do it without you ❤️```""",
        color = 0x654321
    )
    owlcredits.set_thumbnail(url='https://neo-owls.net/images/bot_thumb')
                    
    await ctx.send(embeds=owlcredits, ephemeral=True)

# trade report
# takes in trading data to create entry
@bot.command(
    name="report",
    description="Submit a trade report to OWLS. Press Enter or send the command to bring up a form."
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
    title = 'Is this correct? Press 👍 to finish submitting your report or dismiss this message to discard it. You should only need to press the button once.',
    description = f"`{date}`\n```diff\n~ s: {sent}\n~ r: {received}\n*** notes: {notes}\n*** reported by: {user}```",
    color = 0x654321   
    )               
    send_message.set_thumbnail(url='https://neo-owls.net/images/bot_thumb')
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
 
    await ctx.send(embeds=send_message, components=[b], ephemeral=True)

bot.start()
