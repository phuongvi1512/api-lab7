import sqlite3

def create_db():
    conn = sqlite3.connect('/data/anomalies.sqlite')
    c = conn.cursor()

    #create table event_stats_file
    c.execute('''CREATE TABLE anomaly
                  (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                    event_id VARCHAR(250) NOT NULL,
                    trace_id VARCHAR(250) NOT NULL,
                    event_type VARCHAR(100) NOT NULL,
                    anomaly_type VARCHAR(100) NOT NULL,
                    description VARCHAR(250) NOT NULL,
                    date_created VARCHAR(100) NOT NULL))''')
    
    conn.commit()
    conn.close()