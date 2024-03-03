import mysql.connector

def create_tables(hostname, username, password, db):
    db_conn = mysql.connector.connect(host=hostname, 
                                    user=username,
                                    password=password,
                                    database=db)

    db_cursor = db_conn.cursor()

    db_cursor.execute('''
                CREATE TABLE switch_report
                (id INT NOT NULL AUTO_INCREMENT, 
                trace_id VARCHAR(250) NOT NULL,
                report_id VARCHAR(250) NOT NULL,
                switch_id VARCHAR(250) NOT NULL,
                status VARCHAR(250) NOT NULL,
                temperature INT NOT NULL,
                timestamp VARCHAR(100) NOT NULL,
                date_created VARCHAR(100) NOT NULL,
                CONSTRAINT switch_report_pk PRIMARY KEY (id))      
                ''')

    db_cursor.execute('''
                CREATE TABLE configuration_file
                (id INT NOT NULL AUTO_INCREMENT, 
                trace_id VARCHAR(250) NOT NULL,
                file_id VARCHAR(250) NOT NULL,
                switch_id VARCHAR(250) NOT NULL,
                file_size INT NOT NULL,
                timestamp VARCHAR(100) NOT NULL,
                date_created VARCHAR(100) NOT NULL,
                CONSTRAINT configuration_file_pk PRIMARY KEY (id))
                ''')

    db_conn.commit()
    db_conn.close()