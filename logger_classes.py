"""
logger_classes.py

Purpose:  log data, as [item.TagName,item.Value,Timestamp] triplets, to
          various types of media

"""
import re
import os
import datetime
import traceback
import pandas as pd
from credentials_plclogpoc import get_creds
from googleapiclient.discovery import build

rgx_ur = re.compile(':C(\d+)$')

########################################################################
########################################################################

class PYLOGIX_LOGGER:
    """Base class for logging name/value/timestamp triplets"""

    ################################
    def __init__(self,olds,*args,debug=False,**kwargs):
        """
 olds:  pylogix element list, each with .TagName and .Value attributes
debug:  Set to True to send debugging info to stdout

"""
        assert type(self)!=PYLOGIX_LOGGER,('Base class PYLOGIX_LOGGER'
                                           ' must be sub-classed and'
                                           ' cannot be instantiated'
                                           ' by itself'
                                          )
        self.debug = debug
        self.olds = olds
        for old in self.olds: old.Value = None

    ################################
    def log_news(self,news,*args,**kwargs):
        """
Log changes in tracked values:

  Initialize timestamp and empty list of changed values
  Append [Item,Value,Timestamp] triplets for changed values
  For changed values:
  - Append .Tagname, .Value and timestamp triplet to changed list
  - Update value stored in self.olds
  Call logging method (.__call__) of sub-class

news:  pylogix element list, each with .TagName and .Value attributes

"""
        self.now = datetime.datetime.utcnow().isoformat()[:19]
        self.changeds = list()

        for old,new in zip(self.olds,news):
            if old.Value != new.Value:
                self.changeds.append((new.TagName,new.Value,self.now,))
                old.Value = new.Value

        ### Sub-class must have method .__call__(...)
        self(*args,**kwargs)

########################################################################
########################################################################

class PYLOGIX_LOGGER_FLAT_ASCII(PYLOGIX_LOGGER):
    """Log data to flat ASCII file"""

    ################################
    def __init__(self,log_name,*args
                     ,fmtstr="{0} - {1} - {2}\n"
                     ,**kwargs
                ):
        """
log_name:  path to flat ASCII file
  fmtstr:  format string for Tagname,Value,Timestamp
           - Default string is 'TagName - Value - Timestamp\n'

"""
        self.log_name = log_name
        self.format = fmtstr.format
        super().__init__(*args,**kwargs)

    ################################
    def __call__(self,*args,**kwargs):
        """Append changed data to flat ASCII file"""
        if self.changeds:                  ### Do nothing for no changes
            with open(self.log_name, "a") as fOut:
                for changed in self.changeds:
                    fOut.write(self.format(*changed))

########################################################################
########################################################################

class PYLOGIX_LOGGER_CSV(PYLOGIX_LOGGER_FLAT_ASCII):
    """Log 'TagName,Value,Timestamp' to CSV flat ASCII file"""

    ################################
    def __init__(self,csv_name,*args,**kwargs):
        """
csv_name:  path to CSV file; cf. log_name in PYLOGIX_LOGGER_FLAT_ASCII

"""
        super().__init__(csv_name,*args,fmtstr="{0},{1},{2}\n",**kwargs)

    ### Let PYLOGIX_LOGGER_FLAT_ASCII.__call__ do the work

########################################################################
########################################################################

class PYLOGIX_LOGGER_EXCEL(PYLOGIX_LOGGER):
    """Log 'TagName,Value,Timestamp' to eXcel workbook"""

    ################################
    def __init__(self,xl_name,*args,max_rows=0,**kwargs):
        """
 xl_name:  path to eXcel workbook
max_rows:  approximate limit for number of rows in worksheet
           *** N.B. 0 => no limit

"""
        super().__init__(*args,**kwargs)

        self.xl_name = xl_name
        ### Left-most index of rows to keep
        self.left_index = (max_rows and int(max_rows) > 0
                          ) and -int(max_rows) or 0

    ################################
    def __call__(self,*args,**kwargs):
        """Append changes to eXcel worksheet"""
        if self.changeds:                  ### Do nothing for no changes

            ### Put new data into Pandas DataFrame
            dfnew = pd.DataFrame(self.changeds
                                ,columns='Item Value Timestamp'.split()
                                )
            try:
                ### Read old data from worksheet into Pandas Dataframe
                ### Use same column names for new data
                dfold = pd.read_excel(self.xl_name)
                dfnew.columns = dfold.columns
            except:
                ### On any error reading old data, assume no old data
                dfold = pd.DataFrame([],columns=dfnew.columns)

            ### Append new data to old data, and overwrite eXcel file
            with pd.ExcelWriter(self.xl_name, mode="w") as writer:
                dfold.append(dfnew
                ).iloc[self.left_index:].to_excel(writer,index=False)

########################################################################
########################################################################

class PYLOGIX_LOGGER_GOOGLE_SHEET(PYLOGIX_LOGGER):
    """Log 'TagName,Value,Timestamp' to Google Sheet"""

    ################################
    def __init__(self
                ,*args
                ,SS_ID='1zHFhjtSec0XDO1z-lIhtwBU8O7ZiE9MJIhiBUa-YkAA'
                ,SHEET_NAME='PLCLOGPOC'
                ,TOKEN_FILE='token.pickle'
                ,CREDENTIAL_FILE='credentials.json'
                ,max_rows=200
                ,**kwargs
                ):
        """
          *args:  Initial list of values to log, passed to parent class
          SS_ID:  spreadsheet ID i.e. replace <SS_ID> in URL
                    https://docs.google.com/spreadsheets/d/<SS_ID>
     SHEET_NAME:  sheet in Google Sheet SS_ID.
                    N.B. must be first sheet (0) for .batchUpdate
     TOKEN_FILE:  Pickle file with credentials to write to SS_ID
CREDENTIAL_FILE:  JSON file with credentials to write to SS_ID
       max_rows:  Approx. row count when leading rows will be removed

"""

        super().__init__(*args,**kwargs)

        (self.ss_id,self.name,self.token_file,self.creds_file
        ,) = (SS_ID,SHEET_NAME,TOKEN_FILE,CREDENTIAL_FILE
        ,)

        self.max_rows = max([20,int(max_rows)])
        if self.max_rows > int(max_rows):
            print('Limiting Google Sheet {2} to minimum of {0} rows'
                  ' instead of requested {1} rows'.format(self.max_rows
                                                         ,max_rows
                                                         ,self.ss_id
                                                         )
                 )

        ### Convert credentials to Spreadsheets object
        self.creds = get_creds(TOKEN_FILE=self.token_file
                              ,CREDENTIAL_FILE=self.creds_file
                              )
        self.ssheets = build('sheets', 'v4', credentials=self.creds).spreadsheets()

    ################################
    def __call__(self,*args,**kwargs):
        """Append changes to Google Sheet"""

        if not self.changeds: return       ### Do nothing for no changes

        ### Get Google spreadsheets functions
        append = self.ssheets.values().append
        update = self.ssheets.values().update

        ### Append rows of changed data to Google sheet
        ###
        ###                Columns
        ##            A            B        C
        ###   Row
        ###   1       Item         Value    Timestamp  <= Header
        ###   2       Last-update  <time>   <time>     <= Last update
        ###   3       <name>       <value>  <time>     <= Data
        ###   4       <name>       <value>  <time>     <= Data
        ###   ...                                      ...
        ###
        result = append(spreadsheetId=self.ss_id
                       ,range=f"'{self.name}'!A3"
                       ,body=dict(values=self.changeds)
                       ,valueInputOption="RAW"
                       ,insertDataOption="INSERT_ROWS"
                       ).execute()

        if self.debug: print(dict(append_result=result))

        ### The [result] from the append(...) call above looks like this:
        ###
        ###   {...'updates':{...'updatedRange':'PLCLOGPOC!A41:C46'...}}
        ###
        ### where the ':C46' is the last cell written to, so 46 is the
        ### last of row; compare that to the maximum number of rows
        ### allowed

        updatedRange = result.get('updates',dict()).get('updatedRange','')
        match = rgx_ur.search(updatedRange)
        if not (None is match):
            try:
                last_row_appended = int(match.groups()[-1])
                ### Cheap exception if last row does not exceed limit
                assert self.max_rows < last_row_appended 
                ### Limit number of rows by deleting five at a time,
                ### but first copy a formula to all rows in column D
                batchUpdate = self.ssheets.batchUpdate
                r = batchUpdate(spreadsheetId=self.ss_id
                               ,body={'requests':
                                       [
                                         ### Formula converts timestamp
                                         ### to time
                                         {'repeatCell':
                                           {'range':
                                             {'sheetId':0
                                             ,'startRowIndex':2
                                             ,'endRowIndex':last_row_appended
                                             ,'startColumnIndex':3
                                             ,'endColumnIndex':4
                                             }
                                           ,'cell':
                                             {'userEnteredValue':
                                               {'formulaValue':
                                                     '=if(C3=""'
                                                        ',""'
                                                        ',date(left(C3,4)'
                                                             ',right(left(C3,7),2)'
                                                             ',right(left(C3,10),2)'
                                                             ')'
                                                        '+time(left(right(C3,8),2)'
                                                             ',left(right(C3,5),2)'
                                                             ',right(C3,2)'
                                                             ')'
                                                        ')'
                                               }
                                             }
                                           ,'fields': 'userEnteredValue'
                                           }
                                         }
                                         ### Delete rows 3 to 7 (one-based)
                                         ### = rows 2 to 6 (zero-based)
                                       , {'deleteDimension':
                                           {'range':
                                             {'sheetId':0
                                             ,'dimension':'ROWS'
                                             ,'startIndex':2
                                             ,'endIndex':7
                                             }
                                           }
                                         }
                                       ]
                                     }
                               ).execute()

            except AssertionError as e:
                if self.debug: traceback.print_exc()
            
            except:
                traceback.print_exc()

        ### Update Last-update timestamps on row 2
        update_time = dict(values=[[self.now,self.now]])
        result = update(spreadsheetId=self.ss_id
                       ,range=f"'{self.name}'!B2:C2"
                       ,body=update_time
                       ,valueInputOption="RAW"
                       ).execute()

        if self.debug: print(dict(update_result=result))
