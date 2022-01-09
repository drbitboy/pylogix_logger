"""
simple read list in loop, interval = 0.5 seconds (default)
Read a list of tags, log value changes
"""
import re
import os
import sys
import time
import pylogix
import datetime
#from pycomm3 import SLCDriver
from credentials_plclogpoc import get_creds
from googleapiclient.discovery import build

do_plclogpoc_debug = 'PLCLOGPOC_DEBUG' in os.environ or '--debug' in sys.argv

rgx_ur = re.compile(':C(\d+)$')

########################################################################
########################################################################

class PYLOGIX_LOGGER:
    """Base class for logging name/value pairs with timestamps"""

    def __init__(self,olds,*args,**kwargs):
        assert type(self)!=PYLOGIX_LOGGER,'Class A must be sub-classed and cannot be instantiated itself'
        self.olds = olds
        for old in self.olds: old.Value = None

    def log_news(self,news,*args,**kwargs):
        """
Initialize timestamp and empty list of changed values
Append [Name,Value,Timestamp] triplets for changed values
Log changed values

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
    """Log "Name - Value - Timestamp" to flat ASCII file"""

    def __init__(self,log_name,*args,**kwargs):
        self.log_name = log_name
        super().__init__(*args,**kwargs)

    def __call__(self,*args,**kwargs):
        """Append changes to flat ASCII file"""
        if self.changeds:                  ### Do nothing for no changes
            with open(self.log_name, "a") as fOut:
                for changed in self.changeds:
                    fOut.write("{0} - {1} - {2}\n".format(*changed))

########################################################################
########################################################################

class PYLOGIX_LOGGER_GOOGLE_SHEET(PYLOGIX_LOGGER):
    def __init__(self
                ,*args
                ,SS_ID='1zHFhjtSec0XDO1z-lIhtwBU8O7ZiE9MJIhiBUa-YkAA'
                ,SHEET_NAME='PLCLOGPOC'
                ,TOKEN_FILE='token.pickle'
                ,CREDENTIAL_FILE='credentials.json'
                ,max_rows=200
                ,**kwargs
                ):

        super().__init__(*args,**kwargs)

        self.ss_id = SS_ID
        self.name = SHEET_NAME
        self.token_file = TOKEN_FILE
        self.creds_file = CREDENTIAL_FILE
        self.max_rows = max([20,int(max_rows)])
        if self.max_rows > int(max_rows):
            print('Limiting Google sheet to minimum of {0} rows instead of requested {1} rows'
                 .format(self.max_rows,max_rows)
                 )

        ### Credential => Spreadsheet
        self.creds = get_creds(TOKEN_FILE=self.token_file
                              ,CREDENTIAL_FILE=self.creds_file
                              )
        self.ssheets = build('sheets', 'v4', credentials=self.creds).spreadsheets()

    def __call__(self,*args,**kwargs):

        if not self.changeds: return       ### Do nothing for no changes

        ### Append changed rows to spreadsheet
        append = self.ssheets.values().append
        result = append(spreadsheetId=self.ss_id
                       ,range=f"'{self.name}'!A3"
                       ,body=dict(values=self.changeds)
                       ,valueInputOption="RAW"
                       ,insertDataOption="INSERT_ROWS"
                       ).execute()


        if do_plclogpoc_debug: print(dict(append_result=result))

        ### Limit number of rows by deleting five at a time
        updatedRange = result.get('updates',dict()).get('updatedRange','')
        match = rgx_ur.search(updatedRange)
        if not (None is match):
            try:
                last_row_appended = int(match.groups()[-1])
                assert self.max_rows < last_row_appended   ### cheap exceptions
                batchUpdate = self.ssheets.batchUpdate
                r = batchUpdate(spreadsheetId=self.ss_id
                               ,body={'requests':
                                       [
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

            except AssertionError as e: pass
            except:
                import traceback
                traceback.print_exc()

        ### Update Last-update timestamps on row 2
        update_time = dict(values=[[self.now,self.now]])
        update = self.ssheets.values().update
        result = update(spreadsheetId=self.ss_id
                       ,range=f"'{self.name}'!B2:C2"
                       ,body=update_time
                       ,valueInputOption="RAW"
                       ).execute()

        if do_plclogpoc_debug: print(dict(update_result=result))

########################################################################
########################################################################

if "__main__" == __name__:

    ### Process command-line options

    av1 = sys.argv[1:]

    ### PLC tags to read:  --tag=Tag0=[ --tag=Tag1[...]]

    tags = [a[6:] for a in av1 if a[:6]=='--tag=']

    ### PLC configuration:
    ###
    ###   --ip=192.168.1.10    ### IP address
    ###   --micro8...          ### If PLC is Micro8xx
    ###
    ipaddr = (["192.168.1.10"]
             +[a[5:] for a in av1 if a[:5]=='--ip=']
             )[-1]

    micro8xx = ['--micro8' in [a[:8].lower() for a in av1]]

    ### Inter-sample interval, seconds:  --interval=0.5

    intrvl = float(([0.5]
                   +[a[11:] for a in av1 if a[:11]=='--interval=']
                   )[-1]
                  )

    ### Filename for flat ASCII log:  --flat-ascii=ascii_log.txt

    flatxt = ([False]
             +[a[13:] for a in av1 if a[:13]=='--flat-ascii=']
             )[-1]

    ### Google sheet API - only used if spreadsheet ID is not False
    ###
    ###   --gapi-ssheet-id=...              ### Spreadsheet identifier
    ###   [--gapi-sheet-name=PLCLOGPOC]     ### Sheet name
    ###   [--gapi-pickle=token.pickle]      ### Pickled credentials
    ###   [--gapi-creds=credentials.json]   ### Credentials JSON file
    ###
    ssheet_id = ([False]
                +[a[17:] for a in av1 if a[:17]=='--gapi-ssheet-id=']
                )[-1]

    sheet_name = (['PLCLOGPOC']
                 +[a[18:] for a in av1 if a[:18]=='--gapi-sheet-name=']
                 )[-1]

    pickle_file = (['token.pickle']
                  +[a[14:] for a in av1 if a[:14]=='--gapi-pickle=']
                  )[-1]

    creds_file = (['credentials.json']
                 +[a[13:] for a in av1 if a[:13]=='--gapi-creds=']
                 )[-1]

    max_rows = ([200]
               +[a[16:] for a in av1 if a[:16]=='--gapi-max-rows=']
               )[-1]

    ### Ensure at least one tag is present
    assert tags,"""
Usage:

python pylogix_logger_drbitboy              \\
                                            \\
        ### Tag names to log:               \\
                                            \\
          --tag=TAG0[ --tag=TAG2[ ...]]     \\
                                            \\
        ### PLC connetion information:      \\
                                            \\
          [--ip=192.168.1.10] [--micro8xx]  \\
                                            \\
        ### Flat ASCII log filename:        \\
                                            \\
          [--flat-ascii=...]                \\
                                            \\
        ### Google Sheets:                  \\
                                            \\
          [--gapi-ssheet-id=...]            \\
          [--gapi-sheet-name=...]           \\
          [--gapi-creds=credentials.json]   \\
          [--gapi-pickle=token.pickle]      \\
          [--gapi-max-rows=20]
"""

    with pylogix.PLC(ipaddr) as comm:

        ### Set up pylogix Read options as lambda function
        ### - Micro8xx cannot read sequence of tags; accomplish same via
        ###   list comprehension
        comm.Micro800 = micro8xx
        if micro8xx: R = lambda : [comm.Read(tag) for tag in tags]
        else       : R = lambda : comm.Read(tags).Value

        ### Build list of loggers
        pyloggers = list()

        if flatxt:
            pyloggers.append(PYLOGIX_LOGGER_FLAT_ASCII(flatxt,R()))

        if ssheet_id:
            pyloggers.append(PYLOGIX_LOGGER_GOOGLE_SHEET(R()
                                                        ,SS_ID=ssheet_id
                                                        ,SHEET_NAME=sheet_name
                                                        ,TOKEN_FILE=pickle_file
                                                        ,CREDENTIAL_FILE=creds_file
                                                        ,max_rows=max_rows
                                                        )
                            )

        while True:
            try:

                ### Log new elements if they differ from old elements
                news = R()
                for pylogger in pyloggers: pylogger.log_news(news)

                time.sleep(intrvl)

            except KeyboardInterrupt:
                break                            # stop looping on CTRL+C
