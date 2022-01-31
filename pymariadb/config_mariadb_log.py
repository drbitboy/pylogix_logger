"""
Python script:  config_mariadb_log.py

Purpose:  Ensure PLC data logging table, with 'log' as the name,
          exists in MariaDB/MySQL database named 'test_something'

Usage:  python config_mariadb_log.py test_dbname [--debug]

Prerequisites:

  1) User defaults file

  1.1) E.g. ~/.my.cnf with contents:

          [client]
          user=test

  2) MariaDB/MySQL user 'test' has all privileges
     to databases named test%

  2.1) Cf. MariaDB/MySQL script 'mysql_test_config.mysql'
           - Executed as MariaDB/MySQL user 'root'

"""
import re
import sys
import datetime
import MySQLdb

do_debug = '--debug' in sys.argv[2:]

create_db_query = """
CREATE DATABASE IF NOT EXISTS {0};
"""

create_tbl_queries = """
CREATE TABLE IF NOT EXISTS log
( rowid INT AUTO_INCREMENT PRIMARY KEY
, timestamp DATETIME NOT NULL
, tag_name VARCHAR(32) NOT NULL
, tag_value DOUBLE NOT NULL
);

CREATE INDEX IF NOT EXISTS tag_name   ON log (tag_name);

CREATE INDEX IF NOT EXISTS timestamp  ON log (timestamp);

CREATE INDEX IF NOT EXISTS ts_tag     ON log (tag_name,timestamp);
"""

def config_mariadb_log(dbname):

  ### Validate Database name from command-line
  dbname = sys.argv[1]
  rgx_dbname = re.compile(r'^test[a-zA-Z0-9_]*$')
  assert not (None is rgx_dbname.match(dbname)
             ),'Invalid DB name [{0}]'.format(dbname)

  ### Connect to MariaDB/MySQL server on localhost
  ### - Assume user name is in ~/.my.cnf
  ### ***N.B. No database name specified
  cu=MySQLdb.connect(read_default_group='').cursor()

  ### Execute DATABASE creation query, close connection
  if do_debug: print(create_db_query.format(dbname).strip())
  cu.execute(create_db_query.format(dbname))
  cu.connection.close()
  del cu

  ### Connect to MariaDB/MySQL server with database name
  cu=MySQLdb.connect(database=dbname,read_default_group='').cursor()

  ### Execute TABLE and INDEX creation queries
  if do_debug: print(create_tbl_queries)
  cu.execute(create_tbl_queries)

  ### Describe TABLE
  cu.execute('DESCRIBE log;')
  for row in cu: print(row)

  ### Close connection
  cu.connection.close()
  del cu

if "__main__" == __name__ and sys.argv[1:]:
  config_mariadb_log(sys.argv[1])
