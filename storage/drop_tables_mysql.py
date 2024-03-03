import mysql.connector

db_conn = mysql.connector.connect(host="localhost",
                                  user="user",
                                  password="password",
                                  database="events")

db_cursor = db_conn.cursor()
db_cursor.execute(
                '''
                 DROP TABLE switch_report, configuration_file
                ''')
db_conn.commit()
db_conn.close()