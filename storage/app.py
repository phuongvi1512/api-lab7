from base import Base
from create_tables_mysql import create_tables
from switch_report import SwitchReport
from configuration_file import ConfigurationFile
import yaml,  datetime, json, os
import logging.config
from time import sleep
import connexion
from connexion import NoContent
from connexion.middleware import MiddlewarePosition
from starlette.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine
from sqlalchemy import and_
from sqlalchemy.orm import sessionmaker
from pykafka import KafkaClient
from pykafka.common import OffsetType
from threading import Thread

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

#connect to database mysql
with open('app_conf.yml', 'r') as f: 
    app_config = yaml.safe_load(f.read())
username = app_config['datastore']['user']
password = app_config['datastore']['password']
hostname = app_config['datastore']['hostname']
port = app_config['datastore']['port']
db = app_config['datastore']['db']

#time to sleep and retry count
SLEEP_TIME = app_config['retry']['sleep_time']
MAX_RETRY_COUNT = app_config['retry']['max_count']

# open logging file
with open('log_conf.yml', 'r') as f:
    log_config = yaml.safe_load(f.read())
    logging.config.dictConfig(log_config)
logger = logging.getLogger('basicLogger')

DB_ENGINE = create_engine(f"mysql+pymysql://{username}:{password}@{hostname}:{port}/{db}", pool_size=10, pool_recycle=3600, pool_pre_ping=True)
#add log
logger.info(f"connect to DB {db}. hostname: {hostname}, port: {port}")
#create database and tables if not exist

Base.metadata.bind = DB_ENGINE

DB_SESSION = sessionmaker(bind=DB_ENGINE)

def publish_event_logger():
    content = {
        "code": "0002",
        "trace_id": f"{str(uuid.uuid4())}",
        "timestamp": f"{datetime.now()}",
        "msg_text": "Code 0002. Successfully start and connect to Kafka. Ready to consume messages"
    }
    msg = {
        "code": "0002",
        "datetime": datetime.now().strftime( "%Y-%m-%dT%H:%M:%S"), 
        "payload": content
    }
    msg_str = json.dumps(msg)
    log_producer.produce(str.encode(msg_str))

def add_switch_report(body):
    """ Receives a switch report """
    session = DB_SESSION()
    report = SwitchReport( trace_id=body['trace_id'],
        report_id=body['report_id'], 
        switch_id=body['switch_id'],
        timestamp=body['timestamp'],
        status=body['status'],
        temperature=body['temperature'])

    session.add(report)
    session.commit()
    session.close()

    logger.debug(f"stored event add report {body['trace_id']}")
    return NoContent, 201


def add_config_file(body):
    """ Receive a configuration file """

    session = DB_SESSION()

    cfile = ConfigurationFile(file_id = body['file_id'],
                   switch_id=body['switch_id'],
                   timestamp=body['timestamp'],
                   file_size=body['file_size'],
                   trace_id=body['trace_id'])

    session.add(cfile)
    session.commit()
    session.close()

    #add debug msg
    logger.debug(f"stored event add configuration file {body['trace_id']}")
    return NoContent, 201

def get_config_file_reading(start_timestamp, end_timestamp):
    #if result is returned, return 200, else return 404
    session = DB_SESSION()

    start_timestamp_datetime = datetime.datetime.strptime(start_timestamp, "%Y-%m-%d %H:%M:%S.%f")
    end_timestamp_datetime = datetime.datetime.strptime(end_timestamp, "%Y-%m-%d %H:%M:%S.%f")

    results = session.query(ConfigurationFile).filter(
        and_(ConfigurationFile.date_created >= start_timestamp_datetime,
        ConfigurationFile.date_created < end_timestamp_datetime)
    )
    results_list = [reading.to_dict() for reading in results]

    #add debug msg
    logger.info("Query for Config file reading after %s return %d results" %(start_timestamp, len(results_list)))   
    return results_list, 200

def get_switch_report_reading(start_timestamp, end_timestamp):
    session = DB_SESSION()

    start_timestamp_datetime = datetime.datetime.strptime(start_timestamp, "%Y-%m-%d %H:%M:%S.%f")
    end_timestamp_datetime = datetime.datetime.strptime(end_timestamp, "%Y-%m-%d %H:%M:%S.%f")
    results = session.query(SwitchReport).filter(
        and_(SwitchReport.date_created >= start_timestamp_datetime,
        SwitchReport.date_created < end_timestamp_datetime)
    )

    results_list = [reading.to_dict() for reading in results]

    #add debug msg
    logger.info("Query for switch report reading after %s return %d results" %(start_timestamp, len(results_list)))
    return results_list, 200


def process_messages():
    """ process event messages"""
    # retry logic, wait until kafka is up
    retry_count = 0
    hostname = "%s:%d"%(app_config['events']['hostname'],
                        app_config['events']['port'])
    while retry_count < MAX_RETRY_COUNT:
        #logging when trying to connect to Kafka
        logger.info(f"Trying to connect to Kafka {retry_count + 1}th time")
        try:
            client = KafkaClient(hosts=hostname)
            topic = client.topics[str.encode(app_config['events']['topic'])]
            #publish msg to event_log if successfully start and connect to Kafka
            #ready to consume messages from events topic
            log_topic = client.topics[str.encode(app_config['events']['log_topic'])]
            log_producer = log_topic.get_sync_producer()
            publish_event_logger()

            #create a consumer on a consumer group that only reads new messages
            # (uncommitted messages) when the service restarts (i.e, it doesn't
            # read all the old messages from the history in the message queue)
            consumer = topic.get_simple_consumer(consumer_group=b'event_group',
                                                reset_offset_on_start=False,
                                                auto_offset_reset=OffsetType.LATEST)
            
            for msg in consumer:
                msg_str = msg.value.decode('utf-8')
                msg = json.loads(msg_str)
                logger.info("Message: %s" % msg)

                payload = msg['payload']

                if msg['type'] == 'switch_report':
                    add_switch_report(payload)
                    #add log if success or fail
                    logger.info(f"Added switch report with id {payload['report_id']}")
                elif msg['type'] == 'configuration_file':
                    add_config_file(payload)
                    logger.info(f"Added configuration file with id {payload['file_id']}")
                else:
                    logger.error("Unknown event type: %s" % msg['type'])
                #commit the new message as being read
                consumer.commit_offsets()
            #break the while loop if things work
            break
        except Exception as e:
            logger.error(f"Connection failed the {retry_count + 1}th time, error is {e}")
            retry_count += 1
            #sleep for a number of seconds
            sleep(SLEEP_TIME)


app = connexion.FlaskApp(__name__, specification_dir='')
app.add_api("openapi.yaml", strict_validation=True, validate_responses=True)
app.add_middleware( CORSMiddleware, 
                   position=MiddlewarePosition.BEFORE_EXCEPTION, 
                   allow_origins=["*"], 
                   allow_credentials=True, 
                   allow_methods=["*"], 
                   allow_headers=["*"], )
if __name__ == "__main__":
    tl = Thread(target=process_messages, args=())
    tl.setDaemon(True)
    tl.start()
    app.run(host='0.0.0.0',port=8090)
