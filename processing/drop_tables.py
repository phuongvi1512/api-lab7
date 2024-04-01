import sqlite3

conn = sqlite3.connect('/data/stats.sqlite')

c = conn.cursor()
c.execute('''
          DROP TABLE stats_file
          ''')

conn.commit()
conn.close()