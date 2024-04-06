import os
from datetime import datetime
import requests
import logging
import logging.config
import pytz
import sqlite3
import yaml
import swagger_ui_bundle
from apscheduler.schedulers.background import BackgroundScheduler
import connexion
from connexion import NoContent
from connexion.middleware import MiddlewarePosition
from starlette.middleware.cors import CORSMiddleware
from base import Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from create_db import create_db
from stats_file import StatsFile


# Reading from external configuration files:
if "TARGER_ENV" in os.environ and os.environ["TARGET_ENV"] == "test":
    print("In Test Environment")
    app_conf_file = "/config/app_conf.yml"
    log_conf_file = "/config/log_conf.yml"
else:
    print("In Dev Environment")
    app_conf_file = "app_conf.yml"
    log_conf_file = "log_conf.yml"


# open logging file External Logging Configuration
with open('log_conf.yml', 'r') as f: 
    log_config = yaml.safe_load(f.read()) 
    logging.config.dictConfig(log_config)
logger = logging.getLogger('basicLogger')

logger.info("App Conf file: %s" % app_conf_file)
logger.info("Log Conf file: %s" % log_conf_file)

#read from log_conf.yml
with open('log_conf.yml', 'r') as f:
    log_config = yaml.safe_load(f.read())
    logging.config.dictConfig(log_config)
logger = logging.getLogger('basicLogger')

#read from app_conf.yaml
with open('app_conf.yml', 'r') as f:
    app_config = yaml.safe_load(f.read())
THRESHOLD = app_config['eventstore']['default_threshold']

DB_ENGINE = create_engine(f"sqlite:///{app_config['datastore']['filename']}")
Base.metadata.create_all(DB_ENGINE)

DB_SESSION = sessionmaker(bind=DB_ENGINE)

def get_stats():
    """ Get latest stats from the sqlite database """
    #connect to the sqlite database
    session = DB_SESSION()
    #query the stats_file table to get the latest stats
    stats = session.query(StatsFile).order_by(StatsFile.last_updated.desc()).first()

    if stats is None:
        return {
            "last_updated": 0,
            "num_reports": 0,
            "num_files": 0,
            "max_temp": 0,
            "max_file_size": 0

        }
    print(stats.to_dict())
    #close the connection
    session.close()
    return stats.to_dict(), 200

def populate_stats():
    """ Periodically update stats based on the data from the Data Storage """
    #starting log msg
    logger.info(f"periodically updating stats at {datetime.now()}")

    #read stats from sqlite database
    conn =sqlite3.connect(f'{app_config["datastore"]["filename"]}')
    c = conn.cursor()

    #execute query to return the most recent last_updated from stats_file
    c.execute("SELECT * FROM stats_file ORDER BY last_updated DESC LIMIT 1")
    #c.execute("SELECT last_updated FROM stats_file LIMIT 1") 
    result = c.fetchone()

    #if there is no result, then add the stats file
    if result is None:
        cur_stats = {
            "last_updated": "2024-01-01 23:07:07.912972",
            "num_reports": 0,
            "num_files": 0,
            "max_temp": 0,
            "max_file_size": 0
        }
    else:
        #if there is a result, then get the last_updated and add the stats file
        cur_stats = {
            "last_updated": result[5],
            "num_reports": result[1],
            "num_files": result[2],
            "max_temp": result[3],
            "max_file_size": result[4]
        }

    #close the connection
    conn.close()

    #get current datetime
    cur_time = str(datetime.now())

    #send get request to the Data Storage to get information for newly update data
    report_body = requests.get(f'{app_config["eventstore"]["url"]}/storage_report', 
                            params={'start_timestamp': f'{str(cur_stats["last_updated"])}', 'end_timestamp': cur_time})
    cfile_body = requests.get(f'{app_config["eventstore"]["url"]}/storage_cfile',
                        params={'start_timestamp': f'{str(cur_stats["last_updated"])}', 'end_timestamp': cur_time})

    if report_body.status_code != 200 or cfile_body.status_code != 200:
        logger.error(f"failed to get data from the Data Storage at {datetime.now()}")
        return NoContent, 404
    else:
        #get the json object from the response
        report_info = report_body.json()
        cfile_info = cfile_body.json()

        #publish if over threshold
        if len(report_info) >= THRESHOLD or len(cfile_info) >= THRESHOLD:
            pass


        #log msg number of events received
        logger.info(f"received {len(report_info)} reports and {len(cfile_info)} cfiles at {datetime.now()}")

        #log debug msg for each new event with trace_id
        for report in report_info:
            logger.debug(f"received report with id {report['trace_id']} at {datetime.now()}")

        for cfile in cfile_info:
            logger.debug(f"received report with id {cfile['trace_id']} at {datetime.now()}")
        #calculate updated statistics with current stats and new stats from Storage 
        num_reports = len(report_info) + cur_stats['num_reports']
        max_temp = max([report['temperature'] for report in report_info] + [cur_stats['max_temp']])
        num_files = len(cfile_info) + cur_stats['num_files']
        max_file_size = max([cfile['file_size'] for cfile in cfile_info] + [cur_stats['max_file_size']])

        #log msg for updated stats
        logger.info(f"updated stats num of reports {num_reports}, max temp {max_temp}, num of files {num_files}, and max file size {max_file_size} at {datetime.now()}")

        #write updated stats to sqlite database
        try:
            conn = sqlite3.connect(f'{app_config["datastore"]["filename"]}')
            c = conn.cursor()
            c.execute("INSERT INTO stats_file (num_reports, num_files, max_temp, max_file_size, last_updated) VALUES (?, ?, ?, ?, ?)", (num_reports, num_files, max_temp, max_file_size, cur_time))
            conn.commit()
            conn.close()
        except Exception as e:  
            logger.error(f"failed to insert updated stats to the sqlite database at {datetime.now()} :%s", e)
            return NoContent, 404

        #ending log msg
        logger.info(f"finished updating stats at {datetime.now()}")




def init_scheduler():
    #create a scheduler
    sched = BackgroundScheduler(daemon=True)

    #specify timezone UTC
    timezone = pytz.timezone('UTC')
    #add the scheduler to run the populate_stats every 5 seconds
    sched.add_job(populate_stats, 'interval', seconds=app_config['scheduler']['period_sec'], timezone=timezone)
    #start the scheduler
    sched.start()

app = connexion.FlaskApp(__name__, specification_dir='')
app.add_api("openapi.yaml", strict_validation=True, validate_responses=True)
app.add_middleware( CORSMiddleware, 
                   position=MiddlewarePosition.BEFORE_EXCEPTION, 
                   allow_origins=["*"], 
                   allow_credentials=True, 
                   allow_methods=["*"], 
                   allow_headers=["*"], )

if __name__ == "__main__":
    if not os.path.exists("/data/stats.sqlite"):
        create_db()
    init_scheduler()
    app.run(host='0.0.0.0',port=8100)
