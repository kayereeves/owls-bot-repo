import random
import interactions
import secret
import requests
from interactions import ActionRow, ComponentContext, CommandContext, Client
from nc_bot_sql import *
import asyncio
from timed_count import timed_count

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

# trade history
# returns the 20 most recent trade data of query
@bot.command(name="search",
            description="View up to 20 recent reports for a particular item.",
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
    query = query.replace(",", "")
    trade_results = return_trades(query)
    footer = "Submitting trade reports or searching the database is easy! Just type / to use the commands!"
    if trade_results != False and trade_results[0] > 0:
        response = requests.get('https://neo-owls.net/itemdata/' + query,
                            headers={'Cache-Control': 'no-cache'})

        if response.status_code == 404:
            title_str = trade_results[1]
        else:
            value_data = response.json()
            if value_data['owls_value'] != '':
                title_str = trade_results[1] + "\n(~OWLS value " + value_data['owls_value'] + ")"
            else:
                title_str = trade_results[1] + "\n(no ~OWLS value)"

    if trade_results != False:
        # trade_results[0] is the total results found, trade_results[1] is the embed title, trade_results[2] are the constructed pages
        if trade_results[0] > 0:
            i = 0
            page = interactions.Embed (
                title = title_str,
                description = trade_results[2][0],
                color = 0x654321
            )
        page.set_thumbnail(url='https://neo-owls.net/images/bot_thumb')
        if trade_results[0] < 5:
            page.set_footer(text="Submitting trade reports or searching the database is easy! Just type / to use the commands!")
        elif not ctx.guild_id:
            page.set_footer(text="Only the first 5 results can be displayed via DM. Use OwlBot in a Discord server to see more!")
        else:
            page.set_footer(text="Submitting trade reports or searching the database is easy! Just type / to use the commands!\nPage 1")
        pages = [page]
        try:
            for i in range(1, len(trade_results[2])):
                page = interactions.Embed (
                    title = title_str,
                    description = trade_results[2][i],
                    color = 0x654321   
                )               
                page.set_thumbnail(url='https://neo-owls.net/images/bot_thumb')
                page.set_footer(text="Submitting trade reports or searching the database is easy! Just type / to use the commands!\nPage " + str(i + 1))
                pages.append(page) 
        except IndexError:
            print('womp')

        message = await ctx.send(embeds = pages[0])
        if trade_results[0] > 5 and ctx.guild_id:
            await message.create_reaction('◀')
            await message.create_reaction('▶')
            await message.create_reaction('⏹️')

            i = 0
            j = 0

            for count in timed_count(1.5, start=1):     
                j += 1.5

                if ctx.author in await message.get_users_from_reaction('◀'):
                    if i > 0:
                        i -= 1
                        await message.edit(embeds = pages[i])
                    j = 0
                    await message.remove_reaction_from(emoji='◀', user=ctx.author)
                elif ctx.author in await message.get_users_from_reaction('▶'):
                    if i < len(pages)-1:
                        i += 1
                        await message.edit(embeds = pages[i])
                    j = 0
                    await message.remove_reaction_from(emoji='▶', user=ctx.author)
                elif ctx.author in await message.get_users_from_reaction('⏹️'):
                    await message.remove_all_reactions()
                    break

                #exit if half a minute goes by with no response
                if j > 20:
                    print("byebye!")
                    break

            await message.remove_all_reactions()

    else:
        womp = interactions.Embed (
            title="No results found :(",
            description = '```diff\nSorry, we don\'t have any trade reports for \'' + query + '\' just yet. Please make sure you\'re searching for the full, correct item name!```',
            color = 0x654321
        )
        womp.set_thumbnail(url='https://neo-owls.net/images/bot_thumb')
        womp.set_footer(text=footer)
        await ctx.send(embeds = womp)

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
                    
    await ctx.send(embeds=owl)

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
                    
    await ctx.send(embeds=owlcredits)

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
    if ctx.guild_id:
        user = ctx.author.user.username + "#" + ctx.author.user.discriminator
    else:
        user = ctx.user.username + "#" + ctx.user.discriminator

    #send the data to the database
    result = add_trade(user, sent, received, date, notes)
 
    if not result:
        failed_message = interactions.Embed (
        title = 'Trade report failed! :(',
        description = '```diff\n- Something went wrong, please try again and remember to format the date as YYYY-MM-DD!\n```',
        color = 0x654321  
        )                 
        failed_message.set_thumbnail(url='https://neo-owls.net/images/bot_thumb')
        await ctx.send(embeds=failed_message)
    else:
        success_message = interactions.Embed (
        title = 'Trade reported successfully! :)',
        description = '```diff\n+ The Owls thank you! 🦉\n```',
        color = 0x654321   
        )                 
        success_message.set_thumbnail(url='https://neo-owls.net/images/bot_thumb')
        await ctx.send(embeds=success_message)

print("OwlBot starting up!")
bot.start()
print("OwlBot shutting down!")
