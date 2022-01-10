"""
simple read list in loop, interval = 0.5 seconds (default)
Read a list of tags, log value changes
"""
import sys
import time
import pylogix
import datetime
import logger_classes as LC

if "__main__" == __name__:

    ####################################################################
    ### Start prologue

    ### 1) Process command-line options

    av1 = sys.argv[1:]

    ### 1.1) PLC tags to read:  --tag=Tag0=[ --tag=Tag1[...]]

    tags = [a[6:] for a in av1 if a[:6]=='--tag=']

    ### 1.1.1) Ensure at least one tag was specified

    assert tags,"""
Usage:

python pylogix_logger_drbitboy             \\
                                           \\
       Tag names to log (one required):    \\
                                           \\
         --tag=TAG0[ --tag=TAG2[ ...]]     \\
                                           \\
       PLC connection information:         \\
                                           \\
         [--ip=192.168.1.10]               \\
         [--micro8xx]                      \\
                                           \\
       Logging inter-sample interval, s:   \\
                                           \\
         [--interval=0.5]                  \\
                                           \\
       Flat ASCII log:                     \\
                                           \\
         [--flat-ascii=path.txt]           \\
                                           \\
       CSV Flat ASCII log:                 \\
                                           \\
         [--flat-csv=path.csv]             \\
                                           \\
       eXcel log:                          \\
                                           \\
         [--excel=path.xlsx]               \\
         [--excel-max-rows=0]              \\
                                           \\
         *** N.B. 0 => no limit on rows    \\
                                           \\
       Google Sheets log:                  \\
                                           \\
         [--gapi-ssheet-id=...]            \\
         [--gapi-sheet-name=...]           \\
         [--gapi-creds=credentials.json]   \\
         [--gapi-pickle=token.pickle]      \\
         [--gapi-max-rows=20]              \\
                                           \\
       Debugging:                          \\
                                           \\
         [--debug]

"""
    ### 1.2) PLC configuration:
    ###
    ###   --ip=192.168.1.10    ### IP address
    ###   --micro8...          ### If PLC is Micro8xx
    ###
    ipaddr = (["192.168.1.10"]
             +[a[5:] for a in av1 if a[:5]=='--ip=']
             )[-1]

    micro8xx = ['--micro8' in [a[:8].lower() for a in av1]]

    ### 1.3) Inter-sample interval, seconds:  --interval=0.5

    intrvl = float(([0.5]
                   +[a[11:] for a in av1 if a[:11]=='--interval=']
                   )[-1]
                  )

    ### 1.4) Filename for flat ASCII log:  --flat-ascii=ascii_log.txt

    flatxt = ([False]
             +[a[13:] for a in av1 if a[:13]=='--flat-ascii=']
             )[-1]

    ### 1.5) Filename for CSV log:  --flat-csv=csv_log.csv

    csv = ([False]
          +[a[11:] for a in av1 if a[:11]=='--flat-csv=']
          )[-1]

    ### 1.6) Filename for eXcel log:  --excel=xl_log.xlsx
    ###                               --excel-max-rows=0

    xl = ([False]
          +[a[8:] for a in av1 if a[:8]=='--excel=']
          )[-1]

    xl_max_rows = ([False]
                  +[a[17:] for a in av1 if a[:17]=='--excel-max-rows=']
                  )[-1]

    ### 1.7) Google sheet API - only used if spreadsheet ID is not False
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

    gapi_max_rows = ([200]
                    +[a[16:] for a in av1 if a[:16]=='--gapi-max-rows=']
                    )[-1]

    ### 1.7) PYLOGIX_LOGGER debugging

    debug = '--debug' in av1

    ### 2) Open pylogix communications

    with pylogix.PLC(ipaddr) as comm:

        ### 2.1) Set up pylogix Read options as lambda function
        ### 2.1.1) Micro8xx cannot read sequence of tags; accomplish
        ###        same via list comprehension
        comm.Micro800 = micro8xx
        if micro8xx: R = lambda : [comm.Read(tag) for tag in tags]
        else       : R = lambda : comm.Read(tags).Value

        ### 2.2) Build list of loggers, from logger_classes module
        pyloggers = list()
        app = pyloggers.append

        ### 2.2.1) Flat ASCII log "Name - Value - Timestamp"
        if flatxt:
            app(LC.PYLOGIX_LOGGER_FLAT_ASCII(flatxt,R(),debug=debug))

        ### 2.2.2) CSV log "Name,Value,Timestamp"
        if csv:
            app(LC.PYLOGIX_LOGGER_CSV(csv,R(),debug=debug))

        ### 2.2.3) eXcel workbook log
        if xl:
            app(LC.PYLOGIX_LOGGER_EXCEL(xl
                                       ,R()
                                       ,max_rows=xl_max_rows
                                       ,debug=debug
                                       )
               )

        ### 2.2.4) Google Sheet API log
        if ssheet_id:
            app(LC.PYLOGIX_LOGGER_GOOGLE_SHEET(R()
                                              ,SS_ID=ssheet_id
                                              ,SHEET_NAME=sheet_name
                                              ,TOKEN_FILE=pickle_file
                                              ,CREDENTIAL_FILE=creds_file
                                              ,max_rows=gapi_max_rows
                                              ,debug=debug
                                              )
               )
        ### End prologue
        ################################################################

        ################################################################
        ### Here's the beef:  
        ### - In a loop, log new elements that differ from old elements
        ################################################################

        while True:

            try:
                for pylogger in pyloggers: pylogger.log_news(R())
                time.sleep(intrvl)            ### Wait before repeating

            except KeyboardInterrupt:
                print('\n\n\n')               ### Help cmd line editor
                break                         ### Exit loop on CONTROL+C
