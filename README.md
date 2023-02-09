# Use pylogix module to log PLC data to ASCII (text or CSV), or to spreadsheet (eXcel, or Google) orto  MariaDB/MySQL database

### Usage

    % python pylogix_logger_drbitboy.py        \
                                               \
         --tag=TAG0[ --tag=TAG2[ ...]]         \  Tag names to log (one required)
                                               \
         [--ip=192.168.1.10]                   \  PLC connection information
         [--micro8xx]                          \
                                               \
         [--interval=0.5]                      \  Logging inter-sample interval, s
                                               \
         [--flat-ascii=path.txt]               \  Flat ASCII log
                                               \
         [--flat-csv=path.csv]                 \  CSV Flat ASCII log
                                               \
         [--excel=path.xlsx]                   \  eXcel log
         [--excel-max-rows=0]                  \  *** N.B. 0 => no limit on rows
                                               \
         [--gapi-ssheet-id=...]                \  Google Sheets API (gapi) log
         [--gapi-sheet-name=PLCLOGPOC]         \
         [--gapi-creds=credentials.json]       \  - Cf. [Google API] below
         [--gapi-pickle=token.pickle]          \  - Cf. [Google API] below
         [--gapi-max-rows=20]                  \
                                               \
         [--mysql-db=test_drbitboy]            \  MariaDB/MySQL log; DB name
                                               \
           [--mysql-host=...]                  \ - MySQLdb.connect() keyword args
           [--mysql-user=...]                  \
           [--mysql-password='']               \
           [--mysql-read_default_group='']     \
                                               \
       Debugging:                              \
                                               \
         [--debug]                             \  Turn on debugging to STDOUT

       PLC configuration:

         --ip=192.168.1.10                     \ IP address
         --micro8...                           \ If PLC is Micro8xx
                                               \


e.g. to log data from the CCW/Micro820 program in the image below,

    % python pylogix_logger_drbitboy.py \
    > --tag=year --tag=month --tag=day --tag=hours --tag=minutes --tag=seconds \
    > --ip=192.168.1.160 --micro8 --interval=37 \
    > --gapi-ssheet-id=1zHFhjtSec0XDO1z-lIhtwBU8O7ZiE9MJIhiBUa-YkAA \
    > --gapi-max-rows=25
    > --flat-ascii=/dev/stdout \

![](https://github.com/drbitboy/pylogix_logger/raw/master/images/pylogix_logger_ccw.png)

### MariaDB/MySQL API

See files under sub-directory pymariadb/.

### Google API

### See also

* https://docs.google.com/spreadsheets/d/1zHFhjtSec0XDO1z-lIhtwBU8O7ZiE9MJIhiBUa-YkAA/
  * That string, 1zHFhjtSec0XDO1z-lIhtwBU8O7ZiE9MJIhiBUa-YkAA, is the ... in --gapi-ssheet-id-... above
  * Here is what that sheet looks like
  * ![](https://github.com/drbitboy/pylogix_logger/raw/master/images/PLCLOGPOC_sheet.png)
