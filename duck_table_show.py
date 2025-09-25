import duckdb
from config import Config

# create a connection to a file called 'file.db'
con = duckdb.connect(Config.DB_FILE)
# create a table and load data into it
con.sql("CREATE TABLE test (i INTEGER)")
con.sql("SELECT * FROM incidents")
# query the table
con.table("incidents").show()
# explicitly close the connection
con.close()