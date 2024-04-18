#copy from event_logger

import datetime, json, os
import logging.config
from time import sleep
import yaml
from flask_cors import CORS
import connexion
from connexion import NoContent
from connexion.middleware import MiddlewarePosition
from starlette.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine
from sqlalchemy import and_, func
from sqlalchemy.orm import sessionmaker
from pykafka import KafkaClient
from pykafka.common import OffsetType
from threading import Thread
from base import Base
from create_db import create_db
from event_stats import EventStats

if "TARGER_ENV" in os.environ and os.environ["TARGET_ENV"] == "test":
    print("In Test Environment")
    app_conf_file = "/config/app_conf.yml"
    log_conf_file = "/config/log_conf.yml"
else:
    print("In Dev Environment")
    app_conf_file = "app_conf.yml"
    log_conf_file = "log_conf.yml"

#read from app_conf.yaml
with open('app_conf.yml', 'r') as f:
    app_config = yaml.safe_load(f.read())

# open logging file External Logging Configuration
with open('log_conf.yml', 'r') as f: 
    log_config = yaml.safe_load(f.read()) 
    logging.config.dictConfig(log_config)
logger = logging.getLogger('basicLogger')

logger.info("App Conf file: %s" % app_conf_file)
logger.info("Log Conf file: %s" % log_conf_file)

#time to sleep and retry count
SLEEP_TIME = app_config['retry']['sleep_time']
MAX_RETRY_COUNT = app_config['retry']['max_count']

def get_anomalies(index):
    pass


app = connexion.FlaskApp(__name__, specification_dir='')
app.add_api("openapi.yaml", base_path="/anomaly_detector",strict_validation=True, validate_responses=True)

if "TARGET_ENV" not in os.environ or os.environ["TARGET_ENV"] != "test":
    CORS(app.app)
    app.app.config['CORS_HEADERS'] = 'Content-Type'

if __name__ == "__main__":
    if not os.path.exists("/data/anomalies.sqlite"):
        create_db()
    tl = Thread(target=process_messages, args=())
    tl.setDaemon(True)
    tl.start()
    app.run(host='0.0.0.0',port=8130)