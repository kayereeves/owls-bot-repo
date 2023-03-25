from datetime import datetime
import secrets
import google.auth
import os
import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

import mysql.connector
from mysql.connector import Error

import pandas as pd
import csv
from sqlalchemy import create_engine, types

#items with names of other items in their names
problem_children = {
    'forest clearing background': ['Autumn Forest Clearing Background'],
    'frostbite body paint': ['Baby Frostbite Body Paint'],
    'flower wings': ['Crystalline Flower Wings', 'Holiday Berryflower Wings', 'Mosaic Flower Wings', 'Origami Flower Wings', 'Pressed Flower Wings', 'Stained Glass Flower Wings', 'Sunflower Wings'],
    'gingerbread wings': ['Baby Gingerbread Wings', 'Gingerbread Wings Shower'],
    'greenhouse background': ['Castle Greenhouse Background', 'Dream Greenhouse Background', 'Gothic Castle Greenhouse Background', 'Romantic Greenhouse Background', 'Spring Greenhouse Background'],
    'tree of hearts': ['Pink Tree of Hearts', 'Tree of Hearts Foreground'],
    'grass foreground': ['Hidden Among the Grass Foreground']

}

def runQuery(query, data, is_search=False, return_result=True):
    conn = mysql.connector.connect(
        host=secrets.host,
        user=secrets.user,
        password=secrets.password,
        database=secrets.database
    )
    
    if conn.is_connected():
        with conn:
            if is_search:
                cursor = conn.cursor(buffered=True)
                cursor.execute(query)
            else:
                cursor = conn.cursor(prepared=True)
                cursor.execute(query, data)
            
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

def add_trade(user_id: str, sent: str, received: str, ds=None, notes: str=""):

    query_update = """INSERT INTO transactions(loaded_at, transaction_id, user_id, traded, traded_for, ds, notes) VALUES (%s, %s, %s, %s, %s, %s, %s)"""

    if ds:
        try:
            dt = datetime.strptime(ds, '%Y-%m-%d')
            dt_fin = f"date('{dt}')"

        except Exception as e:
            print(e)
            return False
    else:
        dt = datetime.now().strftime('%Y-%m-%d')
        dt_fin = f"date('{dt}')"
        dt_str = dt

    if not (notes):
        notes = ""

    loaded_ds = 'now()'
    #transaction_id = user_id + datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    transaction_id = "new"
    args = (loaded_ds, transaction_id, user_id, sent, received, dt_fin, notes)


    try:
        runQuery(query_update, args, False)
        #import_bot_data_to_gs([user_id, sent, received, dt_str, notes])
        return True
    except Exception as e:
        print(e)
        return False


def return_trades(query):
    query = query.replace("'", "")
    try:
        item = query.lower()

        if item in problem_children.keys():
            query_retrieve = """SELECT * FROM
                            (SELECT 
                              traded AS item
                              , traded_for AS returned
                              , ds 
                              , notes
                              , user_id
                              FROM transactions
                            WHERE traded LIKE '%""" + item + """%'
                            AND traded NOT LIKE '%Dyeworks %: """ + item + """%'"""
            
            for val in problem_children[item]:
                query_retrieve += " AND traded NOT LIKE '%" + val + "%'"

            query_retrieve += """UNION ALL
                            SELECT 
                              traded AS item
                              , traded_for AS returned
                              , ds
                              , notes
                              , user_id
                              FROM transactions
                            WHERE traded_for LIKE '%""" + item + """%'
                            AND traded_for NOT LIKE '%Dyeworks %: """ + item + """%'"""
            
            for val in problem_children[item]:
                query_retrieve += " AND traded_for NOT LIKE '%" + val + "%'"
            
            query_retrieve += """) trns
                            GROUP BY 1,2,3,4,5
                            ORDER BY ds DESC
                            LIMIT 20;""" 
            
        else:
            query_retrieve = """SELECT * FROM
                            (SELECT 
                              traded AS item
                              , traded_for AS returned
                              , ds 
                              , notes
                              , user_id
                              FROM transactions
                            WHERE traded LIKE '%%%s%%'
                            AND traded NOT LIKE '%%Dyeworks %%: %s%%'
                            UNION ALL
                            SELECT 
                              traded AS item
                              , traded_for AS returned
                              , ds
                              , notes
                              , user_id
                              FROM transactions
                            WHERE traded_for LIKE '%%%s%%'
                            AND traded_for NOT LIKE '%%Dyeworks %%: %s%%') trns
                            GROUP BY 1,2,3,4,5
                            ORDER BY ds DESC
                            LIMIT 20;"""%(item, item, item, item)
        
        results = runQuery(query_retrieve, None, is_search=True)
        print(results)
        cleaned_page_results = ""
        for row in results:
            page_results = "" # page construction
            cleaned_page_results = [] # pages separated into a list
            total_found_results = 0 # total results found
            total_page_results = 0 # total results for current page
            add_result = "" # result to be added to current page
            for row in results:
                # Restrict how many total results are wanted, probably not needed because of the above limit but idk what doesn't kill me makes me stronger
                if total_found_results < 8:
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
                        
                    if row[2] is not None:
                        formatted_date = row[2].strftime('%Y-%m-%d')
                    else:
                        formatted_date = '2000-01-01'
                    # If total_page_results is 5, append that page to the list cleaned_page_results and begin a new page
                    if total_page_results == 8:
                        cleaned_page_results.append(page_results)
                        total_page_results = 0
                        page_results = ""
                        d = '`' + formatted_date + '`\n'
                        add_result = d + '```diff\n' + s + r + n + '\n```\n' # '*** reported by: ' + row[4].replace('"','') + '\n```\n'
                        page_results += add_result
                        total_found_results += 1
                        total_page_results += 1
                    # If total_page_results is less than 5 continue constructing current page
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
                embedTitle = "Displaying " + str(total_found_results) + " recent trade result for '" + item + "':"
            else:
                embedTitle = "Displaying " + str(total_found_results) + " recent trade results for '" + item + "':"
        embed_details = [total_found_results, embedTitle, cleaned_page_results]
        return embed_details
    except Exception as e:
        print(e)
        return False

def return_file(date):
    connection_string = secrets.user + ":" + secrets.password + "@" + secrets.host + "/" + secrets.database
    engine = create_engine(f'mysql+mysqlconnector://{connection_string}')

    file_path = "download.csv"
    query = "select user_id, traded, traded_for, ds, notes from transactions where loaded_at >= '" + date + "' order by loaded_at"
    print(query)

    df = pd.read_sql(sql=query, con=engine)
    df.to_csv(file_path, index=False)
    return True
    
def return_new():
    connection_string = secrets.user + ":" + secrets.password + "@" + secrets.host + "/" + secrets.database
    engine = create_engine(f'mysql+mysqlconnector://{connection_string}')

    file_path = "download.csv"
    query = "select user_id, traded, traded_for, ds, notes from transactions where transaction_id = 'new' order by loaded_at"
    print(query)

    df = pd.read_sql(sql=query, con=engine)
    df.to_csv(file_path, index=False)
    return True

#returns the # of first empty row in the google spreadsheet
def gs_empty_row():
    firstempty = 1

    SCOPES = ['https://www.googleapis.com/auth/drive']
    SPREADSHEET_ID = secrets.sheet_id
    SHEET_NAME = 'Board Data Records!B:E'

    
    #print(list[0]['notes'])

    """Shows basic usage of the Sheets API.
    Prints values from a sample spreadsheet.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    try:
        service = build('sheets', 'v4', credentials=creds)

        # Call the Sheets API
        sheet = service.spreadsheets()
        result = sheet.values().get(spreadsheetId=SPREADSHEET_ID,
                                    range=SHEET_NAME).execute()
        values = result.get('values', [])

        if not values:
            print('No data found.')
            return

        i = 0

        for row in values:
            i += 1
            if not row:
                firstempty = i
                break

    except HttpError as err:
        print(err)

    return firstempty

#todo: fix primary key stuff...
def import_bot_data_to_gs(data):
    SCOPES = ['https://www.googleapis.com/auth/drive']
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    SPREADSHEET_ID = secrets.sheet_id
    empty_row = gs_empty_row()
    SHEET_NAME = 'Board Data Records!A' + str(empty_row) + ':H' + str(empty_row)

    try:
        service = build('sheets', 'v4', credentials=creds)

        values = [
            [
                "bot", data[0], 
                data[1], data[2], 
                data[3], data[4]
            ]
        ]
        body = {
            'values': values
        }
        service.spreadsheets().values().append(
        spreadsheetId=SPREADSHEET_ID, range=SHEET_NAME,
        valueInputOption='USER_ENTERED', body=body).execute()
                
        values = [
            [
                "", "",
                "", "",
                "", ""
            ]
        ]
        body = {
            'values': values
        }
        
        empty_row += 1
        SHEET_NAME = 'Board Data Records!A' + str(empty_row) + ':H' + str(empty_row)
        service.spreadsheets().values().append(
        spreadsheetId=SPREADSHEET_ID, range=SHEET_NAME,
        valueInputOption='USER_ENTERED', body=body).execute()
                
    except HttpError as error:
            print(f"An error occurred: {error}")
