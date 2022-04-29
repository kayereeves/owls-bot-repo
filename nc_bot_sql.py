from datetime import datetime

import mysql.connector
from mysql.connector import Error

import pandas as pd
import csv
from sqlalchemy import create_engine, types

def runQuery(query, return_result=True):
    conn = mysql.connector.connect(
        host="owls-db.c9hvuhvpnktp.us-west-2.rds.amazonaws.com",
        user="owls",
        password="vHAxYRzjZYSEr6E",
        database="owls"
    )
    
    if conn.is_connected():
        cursor = conn.cursor()
        cursor.execute(query)
        if return_result:
            try:
                results = cursor.fetchall()
                conn.close()
                return results
            except:
                conn.close()
                return none

    conn.commit()
    conn.close()
    return None


def add_trade(user_id, sent, received, ds=None, notes=None):
    query_update = "INSERT INTO transactions(loaded_at, transaction_id, user_id, traded, traded_for, ds, notes) VALUES (%s, '%s', '%s', '%s', '%s', %s, '%s')"

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

    if not (notes):
        notes = ""

    loaded_ds = 'now()'
    #transaction_id = user_id + datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    transaction_id = "new"
    args = (loaded_ds, transaction_id, user_id, sent, received, dt_fin, notes)


    try:
        runQuery(query_update %args, False)
        return True
    except Exception as e:
        print(e)
        return False


def return_trades(query):
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
                            LIMIT 20;""" %(item, item, item, item)
        results = runQuery(query_retrieve)
        cleaned_page_results = ""
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
                        
                    if row[2] is not None:
                        formatted_date = row[2].strftime('%Y-%m-%d')
                    else:
                        formatted_date = '2000-01-01'
                    # If total_page_results is 4, append that page to the list cleaned_page_results and begin a new page
                    if total_page_results == 4:
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

def return_file(date):
    connection_string = 'owls:vHAxYRzjZYSEr6E@owls-db.c9hvuhvpnktp.us-west-2.rds.amazonaws.com/owls'
    engine = create_engine(f'mysql+mysqlconnector://{connection_string}')

    file_path = "download.csv"
    query = "select user_id, traded, traded_for, ds, notes from transactions where loaded_at >= '" + date + "' order by loaded_at"
    print(query)

    df = pd.read_sql(sql=query, con=engine)
    df.to_csv(file_path, index=False)
    return True
    
def return_new():
    connection_string = 'owls:vHAxYRzjZYSEr6E@owls-db.c9hvuhvpnktp.us-west-2.rds.amazonaws.com/owls'
    engine = create_engine(f'mysql+mysqlconnector://{connection_string}')

    file_path = "download.csv"
    query = "select user_id, traded, traded_for, ds, notes from transactions where transaction_id = 'new' order by loaded_at"
    print(query)

    df = pd.read_sql(sql=query, con=engine)
    df.to_csv(file_path, index=False)
    return True
