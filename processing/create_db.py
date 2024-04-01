import sqlite3

def create_db():
    conn = sqlite3.connect('/data/stats.sqlite')
    c = conn.cursor()

    #create table stats_file
    c.execute('''CREATE TABLE stats_file
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                num_reports INTEGER NOT NULL, 
                num_files INTEGER NOT NULL, 
                max_temp INTEGER NOT NULL, 
                max_file_size INTEGER NOT NULL,
                last_updated TIMESTAMP NOT NULL))''')
    
    conn.commit()
    conn.close()
