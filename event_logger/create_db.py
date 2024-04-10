import sqlite3

def create_db():
    conn = sqlite3.connect('/data/event_stats.sqlite')
    c = conn.cursor()

    #create table event_stats_file
    c.execute('''CREATE TABLE event_stats_file
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                trace_id VARCHAR(250) NOT NULL, 
                message_code VARCHAR(250) NOT NULL,
                message VARCHAR(250) NOT NULL, 
                last_updated TIMESTAMP NOT NULL))''')
    
    conn.commit()
    conn.close()