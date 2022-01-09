import os
import datetime
import credentials_plclogpoc as cp
from googleapiclient.discovery import build

do_debug = 'PLCLOGPOC_DEBUG' in os.environ

########################################################################
########################################################################

def append_row(item_name='test-name'
              ,item_value=-99
              ,SHEET_NAME='PLCLOGPOC'
              ,SSHEET_ID='1zHFhjtSec0XDO1z-lIhtwBU8O7ZiE9MJIhiBUa-YkAA'
              ):


    ### Build one row of data:  item name; item value; timestamp
    now = datetime.datetime.utcnow().isoformat()[:19]
    body = dict(values=[[item_name,item_value,now]])

    ### Build row of data:  item name; item value; timestamp
    ss=build('sheets', 'v4', credentials=cp.get_creds()).spreadsheets()

    ### Append row to spreadsheet
    result = ss.values().append(spreadsheetId=SSHEET_ID
                               ,range=f"'{SHEET_NAME}'!A3"
                               ,body=body
                               ,valueInputOption="RAW"
                               ,insertDataOption="INSERT_ROWS"
                               ).execute()
    #print(result)

    ### Update Last-update timestamps on row 2
    update_time = dict(values=[[now,now]])
    result = ss.values().update(spreadsheetId=SSHEET_ID
                               ,range=f"'{SHEET_NAME}'!B2:C2"
                               ,body=update_time
                               ,valueInputOption="RAW"
                               ).execute()
    #print(result)
