import interactions
import secret
import requests
from interactions import Status, SlashCommandOption, OptionType, Activity, ModalContext, ShortText, ParagraphText, ButtonStyle
from interactions.ext.paginators import Paginator
from nc_bot_sql import *
import pytz
import re

tok = secret.tok
bot = interactions.Client(token=tok, status=Status.ONLINE, activity=Activity(name="ko-fi.com/owlsnc🦉"))

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
@interactions.slash_command(name="search",
            description="View up to 20 recent reports for a particular item.",
            options=[
            SlashCommandOption(
                name="query",
                description="The item you wish to view reports for.",
                type=OptionType.STRING,
                required=True
            )
            ],
)
            
async def search(ctx: interactions.SlashContext, query):
    is_banned = await banned_user(ctx)

    if is_banned:
        return
    
    query = query.replace(",", "")
    trade_results = return_trades(query)
    footer = "Submitting trade reports or searching the database is easy! Just type / to use the commands!"

    #if trade_results != False and trade_results[0] > 0:
        #title_str = trade_results[1]

        #response = requests.get('https://neo-owls.net/itemdata/' + query,
                            #headers={'Cache-Control': 'no-cache'})

        #if response.status_code == 404:
            #title_str = trade_results[1]
        #else:
            #value_data = response.json()
            #if value_data['owls_value'] != '':
                #title_str = trade_results[1] + "\n(OWLS value: " + value_data['owls_value'] + ")"
            #else:
                #title_str = trade_results[1] + "\n(no OWLS Value)"

    if trade_results != False:
        title_str = trade_results[1]
        
        # trade_results[0] is the total results found, trade_results[1] is the embed title, trade_results[2] are the constructed pages
        if trade_results[0] > 0:
            i = 0
            page = interactions.Embed (
                title = title_str,
                description = trade_results[2][0],
                color = 0x58e2bb
            )
        page.set_thumbnail(url='https://i.imgur.com/kpdvrT9.png')
        if trade_results[0] < 5:
            page.set_footer(text="Submitting trade reports or searching the database is easy! Just type / to use the commands!")
        else:
            page.set_footer(text="Submitting trade reports or searching the database is easy! Just type / to use the commands!\nPage 1")
        pages = [page]
        try:
            for i in range(1, len(trade_results[2])):
                page = interactions.Embed (
                    title = title_str,
                    description = trade_results[2][i],
                    color = 0x58e2bb   
                )               
                page.set_thumbnail(url='https://i.imgur.com/kpdvrT9.png')
                page.set_footer(text="Submitting trade reports or searching the database is easy! Just type / to use the commands!\nPage " + str(i + 1))
                pages.append(page) 
        except IndexError:
            print('womp')

        paginator = Paginator.create_from_embeds(bot, *pages)
        paginator.default_button_color = ButtonStyle.GREEN

        #if (len(pages) > 1):
            #paginator.timeout_interval = 120
            
        await paginator.send(ctx)

    else:
        womp = interactions.Embed (
            title="No results found :(",
            description = '```diff\nSorry, we don\'t have any trade reports for \'' + query + '\' just yet. Please make sure you\'re searching for the full, correct item name!```',
            color = 0x58e2bb
        )
        womp.set_thumbnail(url='https://i.imgur.com/kpdvrT9.png')
        womp.set_footer(text=footer)
        await ctx.send(embeds = womp)

# trade history
# returns the 20 most recent trade data of query
@interactions.slash_command(name="lax-search",
            description="View recent reports containing your search term via lax/non-specific method.",
            options=[
            SlashCommandOption(
                name="query",
                description="The item you wish to view reports for.",
                type=OptionType.STRING,
                required=True
            )
            ],
)
            
async def lax_search(ctx: interactions.SlashContext, query):
    is_banned = await banned_user(ctx)

    if is_banned:
        return
    
    query = query.replace(",", "")
    trade_results = return_trades(query, lax=True)
    footer = "Submitting trade reports or searching the database is easy! Just type / to use the commands!"

    #if trade_results != False and trade_results[0] > 0:
        #response = requests.get('https://neo-owls.net/itemdata/' + query,
                            #headers={'Cache-Control': 'no-cache'})

        #if response.status_code == 404:
            #title_str = trade_results[1]
        #else:
            #value_data = response.json()
            #if value_data['owls_value'] != '':
                #title_str = trade_results[1] + "\n(OWLS value: " + value_data['owls_value'] + ")"
            #else:
                #title_str = trade_results[1] + "\n(no OWLS Value)"

    if trade_results != False:
        title_str = trade_results[1]

        # trade_results[0] is the total results found, trade_results[1] is the embed title, trade_results[2] are the constructed pages
        if trade_results[0] > 0:
            i = 0
            page = interactions.Embed (
                title = title_str,
                description = trade_results[2][0],
                color = 0x58e2bb
            )
        page.set_thumbnail(url='https://i.imgur.com/kpdvrT9.png')
        if trade_results[0] < 5:
            page.set_footer(text="Submitting trade reports or searching the database is easy! Just type / to use the commands!")
        else:
            page.set_footer(text="Submitting trade reports or searching the database is easy! Just type / to use the commands!\nPage 1")
        pages = [page]
        try:
            for i in range(1, len(trade_results[2])):
                page = interactions.Embed (
                    title = title_str,
                    description = trade_results[2][i],
                    color = 0x58e2bb   
                )               
                page.set_thumbnail(url='https://i.imgur.com/kpdvrT9.png')
                page.set_footer(text="Submitting trade reports or searching the database is easy! Just type / to use the commands!\nPage " + str(i + 1))
                pages.append(page) 
        except IndexError:
            print('womp')

        paginator = Paginator.create_from_embeds(bot, *pages)
        paginator.default_button_color = ButtonStyle.GREEN

        #if (len(pages) > 1):
            #paginator.timeout_interval = 120
            
        await paginator.send(ctx)

    else:
        womp = interactions.Embed (
            title="No results found :(",
            description = '```diff\nSorry, we don\'t have any trade reports for \'' + query + '\' just yet. Please make sure you\'re searching for the full, correct item name!```',
            color = 0x58e2bb
        )
        womp.set_thumbnail(url='https://i.imgur.com/kpdvrT9.png')
        womp.set_footer(text=footer)
        await ctx.send(embeds = womp)

#help command
@interactions.slash_command(
    name="owl",
    description = "View a list of commands."
)

async def owl(ctx: interactions.SlashContext):
    is_banned = await banned_user(ctx)

    if is_banned:
        return
    
    owl = interactions.Embed (
        title = 'OwlBot Reloaded Help',
        description = 
        """This bot helps record and display NC trade report data submitted by the community. Type `/` followed by a command to interact with the bot.

        **/report**
        ```\nSubmit a trade report. You will be prompted to input what you sent and what you received.\n\nYou may also choose to add a note to your report as well as record the date in YYYY-MM-DD format.```
        **/search**
        ```\nSearch the database. You will be prompted to input the item which you wish to view trade reports for.```
        **/lax-search**
        ```\nSearch the database via non-specific method. Useful when searching for partial names, e.g.: "nostalgic plushie"```
        **/board-post**
        ```\nSearch the database and return an OWLS NeoBoard-style VC, with dates and values only.```
        **/credits**
        ```\nView credits for OwlBot Reloaded.```""",
        color = 0x58e2bb
    )
    owl.set_thumbnail(url='https://i.imgur.com/kpdvrT9.png')
                    
    await ctx.send(embeds=owl)

#credits command            
@interactions.slash_command(
    name="credits",
    description="View credits for OwlBot Reloaded."
)            

async def owlcredits(ctx: interactions.SlashContext):
    is_banned = await banned_user(ctx)

    if is_banned:
        return
    
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
        ```\nthanks for submitting your trades to us, we couldn't do it without you ❤️```
        \nNEOPETS and all related indicia are trademarks of Neopets, Inc., © 1999-2024.\n\nOwls is a volunteer project run by fans, for fans. If you would like to help support us monetarily, please check out our Ko-Fi page at https://ko-fi.com/owlsnc 🤗""",
        color = 0x58e2bb
    )
    owlcredits.set_thumbnail(url='https://i.imgur.com/kpdvrT9.png')
                    
    await ctx.send(embeds=owlcredits)

# trade report
# takes in trading data to create entry
@interactions.slash_command(
    name="report",
    description="Submit a trade report to OWLS. Press Enter or send the command to bring up a form."
)

async def report(ctx: interactions.SlashContext):
    is_banned = await banned_user(ctx)

    if is_banned:
        return
    
    try:
        report_modal = interactions.Modal(
            ParagraphText(
                label="Sent (Full item names & personal values!)",
                custom_id="sent",
                placeholder="Plz follow format or report may not appear in searches! Ex.: Item (1-2) + Another Item (10) + 2 GBCs",
                min_length=1,
                max_length=500
            ),
            ParagraphText(
                label="Received (Full item names & personal values!)",
                custom_id="received",
                placeholder="Plz follow format or report may not appear in searches! Ex.: Item (1-2) + Another Item (10) + 2 GBCs",
                min_length=1,
                max_length=500
            ),
            ParagraphText(
                label="Notes",
                custom_id="notes",
                placeholder="Notes are moderated and may not include spam or vulgar material. Inappropriate notes risk a ban!",
                required=False,
                min_length=0,
                max_length=200
            ),
            ShortText(
                label="Date (YYYY-MM-DD format only please)",
                custom_id="date",
                value=datetime.now(pytz.timezone('US/Pacific')).strftime('%Y-%m-%d'),
                min_length=10,
                max_length=10
            ),
            title = "Report a Neocash trade to OWLS",
            custom_id = "report" + "." + ctx.user.id.__str__() + "." + datetime.now().strftime("%m/%d/%Y, %H:%M:%S")
        )

        user_modal = interactions.Modal(
            ParagraphText(
                label="Neopets Username",
                custom_id="neo_user",
                placeholder="You will only be asked for this once and it will only be visible to Owls staff members.",
                min_length=1,
                max_length=20
            ),
            title = "Howdy stranger! 🤠",
            custom_id = "username_entry" + "." + ctx.user.id.__str__() + "." + datetime.now().strftime("%m/%d/%Y, %H:%M:%S")
        )

        #check if a user has registered their Neopets username with Owls already. if not, they will need to provide one before
        #they can submit a report.
        if not userCheck(ctx.user.id.__str__()):
            await ctx.send_modal(modal=user_modal)
            user_modal_ctx: ModalContext = await ctx.bot.wait_for_modal(user_modal)
            add_success = add_user(ctx.user.id.__str__(), user_modal_ctx.responses['neo_user'])

            if add_success:
                register_message = interactions.Embed (
                title = 'Thank you for registering your Neopets username!',
                description = '```diff\n+ If you want to change or remove this later just contact an Owls team member! Use the /report command again to submit your trade report.\n```',
                color = 0x58e2bb  
                )
                await user_modal_ctx.send(embeds=register_message)
            else:
                register_failed = interactions.Embed (
                title = 'Something went wrong :(',
                description = '```diff\n- Please try again!\n```',
                color = 0x58e2bb  
                )
                await user_modal_ctx.send(embeds=register_failed)

            return

        await ctx.send_modal(modal=report_modal)
        modal_ctx: ModalContext = await ctx.bot.wait_for_modal(report_modal)
        success = await modal_respond(ctx, modal_ctx.responses['sent'], modal_ctx.responses['received'], modal_ctx.responses['notes'], modal_ctx.responses['date'])
    
        if not success:
            failed_message = interactions.Embed (
            title = 'Trade report failed! :(',
            description = '```diff\n- Something went wrong, please try again and remember to format the date as YYYY-MM-DD!\n```',
            color = 0x58e2bb  
            )                 
            failed_message.set_thumbnail(url='https://i.imgur.com/kpdvrT9.png')
            await modal_ctx.send(embeds=failed_message)
        else:
            success_message = interactions.Embed (
            title = 'Trade reported successfully! :)',
            description = '```diff\n+ The Owls thank you! 🦉\n```',
            color = 0x58e2bb   
            )                 
            success_message.set_thumbnail(url='https://i.imgur.com/kpdvrT9.png')
            await modal_ctx.send(embeds=success_message)
    except:
        print("exception occurred")
        except_message = interactions.Embed (
        title = 'Something went wrong :(',
        description = '```diff\n- Something went wrong, please send the command again!\n```',
        color = 0x58e2bb
        )     
        except_message.set_thumbnail(url='https://i.imgur.com/kpdvrT9.png')
        await ctx.send(embeds=except_message)

async def modal_respond(ctx: interactions.SlashContext, sent: str, received: str, notes:str, date:str):
    neo_user = getUser(ctx.user.id.__str__())

    #send the data to the database
    result = add_trade(neo_user, sent, received, date, notes)
 
    if not result:
        return False
    else:
        return True
    
#searches the database and returns an OWLS NeoBoard-style VC, with dates and values only
@interactions.slash_command(
        name="board-post",
        description="Searches the database and returns an OWLS NeoBoard-style VC, with dates and values only.",
        options=[
            SlashCommandOption(
                name="query",
                description="The item you wish to view reports for.",
                type=OptionType.STRING,
                required=True
            )
            ],
)

async def board_post(ctx: interactions.SlashContext, query):
    is_banned = await banned_user(ctx)

    if is_banned:
        return
    
    query = query.replace(",", "")
    query = query.lower()
    trade_results = data_for_board_post(query)[:5] #the first 5 trade results
    formatted_string = query + '\n'

    if len(trade_results) == 0:
        formatted_string += "No data, please consider reporting if you find a trade!" + '\n'

    else:
        for row in trade_results:
            #if date is present
            if row[2]:
                formatted_date = row[2].strftime('%Y-%m-%d')
            #if date is blank
            else:
                formatted_date = "no date"
        
            formatted_string += formatted_date + ': '

            #if item found in sent
            if query in str(row[0]).lower():
                index = row[0].lower().find(query)
                item_in_trade = row[0][index:]
                value = item_in_trade[item_in_trade.find('(')+1:item_in_trade.find(')')]
            #if item found in received
            else:
                index = row[1].lower().find(query)
                item_in_trade = row[1][index:]
                value = item_in_trade[item_in_trade.find('(')+1:item_in_trade.find(')')]

            formatted_string += value + '\n'

    post = interactions.Embed (
        title = "NeoBoard-style VC data for " + query + ':',
        description = formatted_string,
        color = 0x58e2bb
    )
    await ctx.send(content=formatted_string)

async def banned_user(ctx):
    uid = ctx.user.id.__str__()
    if isBanned(uid):
        reason = banReason(uid)
        banned_message = interactions.Embed (
        title = 'Sorry, you are banned from using OwlBot.',
        description = '```diff\nYour account has been banned from accessing OwlBot for the following reason:\n\n-' + reason + '\n\nIf you would like to appeal this, please contact an Owls team member.\n```',
        color = 0xff0000
        )
        await ctx.send(embeds=banned_message, ephemeral=True)
        return True
    return False

print("\nOwlBot starting up!\n")
bot.start()
print("\nOwlBot shutting down!\n")