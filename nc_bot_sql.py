from datetime import datetime
import secret
import mysql.connector
from mysql.connector import Error
import pandas as pd
import csv
from sqlalchemy import create_engine, types, text

#check if a user is in the database already
def userCheck(user_id):
    query = "SELECT * FROM registered_users WHERE discord_id LIKE " + "'" + user_id + "';"
    if runQuery(query, is_search=True):
        return True
    else:
        return False
    
def getUser(user_id):
    query = "SELECT * FROM registered_users WHERE discord_id LIKE " + "'" + user_id + "';"
    res = runQuery(query, is_search=True)
    return res[0][1]

def isBanned(user_id):
    query = "SELECT * FROM banned_users WHERE discord_id LIKE " + "'" + user_id + "';"
    if runQuery(query, is_search=True):
        return True
    else:
        return False
    
def banReason(user_id):
    query = "SELECT * FROM banned_users WHERE discord_id LIKE " + "'" + user_id + "';"
    res = runQuery(query, is_search=True)
    return res[0][1]

def runQuery(query, data=None, is_search=False, return_result=True):
    conn = mysql.connector.connect(
        host=secret.host,
        user=secret.user,
        password=secret.password,
        database=secret.database
    )
    
    if conn.is_connected():
        with conn:
            if is_search:
                cursor = conn.cursor(buffered=True)
                cursor.execute(query)
            else:
                cursor = conn.cursor(prepared=True)
                cursor.execute(query, data)
                conn.commit()
            
            if return_result:
                try:
                    results = cursor.fetchall()
                    cursor.close()
                    conn.close()
                    return results
                except:
                    cursor.close()
                    conn.close()
                    return None

            conn.commit()
            conn.close()
    return None

def add_user(discord_id: str, neo_username: str):
    sanitized_user = neo_username

    bad_chars = ['<','>','/','\\','"',"'",'?',';']

    for c in bad_chars:
        sanitized_user = sanitized_user.replace(c, '')

    query = """INSERT INTO registered_users(discord_id, neo_user) VALUES (%s, %s)"""
    args = (discord_id, sanitized_user)
    try:
        runQuery(query, args)
        return True
    except Exception as e:
        print(e)
        return False

def add_trade(user_id: str, sent: str, received: str, ds=None, notes: str=""):
    query_update = """INSERT INTO transactions(loaded_at, transaction_id, user_id, traded, traded_for, ds, notes) VALUES (%s, %s, %s, %s, %s, %s, %s)"""

    if ds:
        try:
            dt = datetime.strptime(ds, '%Y-%m-%d')

        except Exception as e:
            print(e)
            return False
    else:
        dt = datetime.now().strftime('%Y-%m-%d')

    if not (notes):
        notes = ""

    loaded_ds = datetime.now().strftime('%Y-%m-%d')
    transaction_id = "new"
    args = (loaded_ds, transaction_id, user_id, sent, received, dt, notes)

    try:
        runQuery(query_update, args)
        return True
    
    except Exception as e:
        print(e)
        return False

def return_trades(query, lax=False):
    #really don't like this but trying to execute it as a prepared statement
    #was making my head explode and there's no good reason these should be in an
    #item search anyway
    bad_chars = ['<','>','/','\\','"',"'",'?',';']

    for c in bad_chars:
        query = query.replace(c, '')

    try:
        item = query.lower()

        if lax:
            #print("lax search")
            query_retrieve = """SELECT * FROM
                            (SELECT 
                              traded AS item
                              , traded_for AS returned
                              , ds 
                              , notes
                              , user_id
                              FROM transactions
                            WHERE traded LIKE '%%%s%%'
                            UNION ALL
                            SELECT 
                              traded AS item
                              , traded_for AS returned
                              , ds
                              , notes
                              , user_id
                              FROM transactions
                            WHERE traded_for LIKE '%%%s%%') trns
                            GROUP BY 1,2,3,4,5
                            ORDER BY ds DESC
                            LIMIT 20;""" %(item, item)

        else:
            query_retrieve = """SELECT * FROM
                            (SELECT 
                              traded AS item
                              , traded_for AS returned
                              , ds 
                              , notes
                              , user_id
                              FROM transactions
                            WHERE traded LIKE '% + """ + item + """ (%) + %'
                            OR traded LIKE '""" + item + """ (%)%'
                            OR traded LIKE '% + """ + item + """ (%)'"""

            query_retrieve += """UNION ALL
                            SELECT 
                              traded AS item
                              , traded_for AS returned
                              , ds
                              , notes
                              , user_id
                              FROM transactions
                            WHERE traded_for LIKE '% + """ + item + """ (%) + %'
                            OR traded_for LIKE '""" + item + """ (%)%'
                            OR traded_for LIKE '% + """ + item + """ (%)'"""
            
            query_retrieve += """) trns
                            GROUP BY 1,2,3,4,5
                            ORDER BY ds DESC
                            LIMIT 20;""" 
        
        results = runQuery(query_retrieve, None, is_search=True)
        #print(results)
        cleaned_page_results = ""
        embed_details = False
        for row in results:
            page_results = "" # page construction
            cleaned_page_results = [] # pages separated into a list
            total_found_results = 0 # total results found
            total_page_results = 0 # total results for current page
            add_result = "" # result to be added to current page
            for row in results:
                # Restrict how many total results are wanted, probably not needed because of the above limit but idk what doesn't kill me makes me stronger
                if total_found_results < 20:
                    if item in str(row[0]).lower():
                        s = '! s: ' + row[0].replace('"','') + '\n'
                    else:
                        s = '~ s: ' + row[0].replace('"','') + '\n'
                    if item in str(row[1]).lower():
                        r = '! r: ' + row[1].replace('"','') + '\n'
                    else:
                        r = '~ r: ' + row[1].replace('"','') + '\n'
                    if row[3]:
                        n = '*** notes: ' + row[3].replace('"','') + '\n'
                    else:
                        n = ''
                    if row[2]:
                        formatted_date = row[2].strftime('%Y-%m-%d')
                    else:
                        formatted_date = "unknown date"
                    # If total_page_results is 5, append that page to the list cleaned_page_results and begin a new page
                    if total_page_results == 5:
                        cleaned_page_results.append(page_results)
                        total_page_results = 0
                        page_results = ""
                        d = '`' + formatted_date + '`\n'
                        add_result = d + '```diff\n' + s + r + n + '\n```\n' # '*** reported by: ' + row[4].replace('"','') + '\n```\n'
                        page_results += add_result
                        total_found_results += 1
                        total_page_results += 1
                    # If total_page_results is less than 4 continue constructing current page
                    else:
                        if formatted_date in page_results:
                            d = ''
                        else:
                            d = '`' + formatted_date + '`\n'
                        add_result = d + '```diff\n' + s + r + n + '\n```\n' # '*** reported by: ' + row[4].replace('"','') + '\n```\n'
                        page_results += add_result
                        total_found_results += 1
                        total_page_results += 1
                else:
                    break
            # Append a final/only page that is not full
            cleaned_page_results.append(page_results)
            if total_found_results == 1:
                embedTitle = str(total_found_results) + " recent trade result for '" + item + "':"
            else:
                embedTitle = str(total_found_results) + " recent trade results for '" + item + "':"
            embed_details = [total_found_results, embedTitle, cleaned_page_results]
        return embed_details
    except Exception as e:
        print(e)
        return False

#returns unformatted data for board vc command
def data_for_board_post(query):
    bad_chars = ['<','>','/','\\','"',"'",'?',';']

    for c in bad_chars:
        query = query.replace(c, '')

    try:
        item = query.lower()

        query_retrieve = """SELECT * FROM
                            (SELECT 
                              traded AS item
                              , traded_for AS returned
                              , ds 
                              , notes
                              , user_id
                              FROM transactions
                            WHERE traded LIKE '% + """ + item + """ (%) + %'
                            OR traded LIKE '""" + item + """ (%)%'
                            OR traded LIKE '% + """ + item + """ (%)'"""

        query_retrieve += """UNION ALL
                            SELECT 
                              traded AS item
                              , traded_for AS returned
                              , ds
                              , notes
                              , user_id
                              FROM transactions
                            WHERE traded_for LIKE '% + """ + item + """ (%) + %'
                            OR traded_for LIKE '""" + item + """ (%)%'
                            OR traded_for LIKE '% + """ + item + """ (%)'"""
            
        query_retrieve += """) trns
                            GROUP BY 1,2,3,4,5
                            ORDER BY ds DESC
                            LIMIT 20;"""
        
        results = runQuery(query_retrieve, None, is_search=True)
        return results
        
    except Exception as e:
        print(e)
        return False