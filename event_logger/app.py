import datetime, json, os
import logging.config
from time import sleep
import yaml
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

# open logging file
with open('log_conf.yml', 'r') as f:
    log_config = yaml.safe_load(f.read())
    logging.config.dictConfig(log_config)
logger = logging.getLogger('basicLogger')



def add_event_stats(body):
    """ Receives event and record in database """
    DB_ENGINE = create_engine(f"sqlite:///{app_config['datastore']['filename']}")
    Base.metadata.create_all(DB_ENGINE)

    DB_SESSION = sessionmaker(bind=DB_ENGINE)
    session = DB_SESSION()
    event_record = EventStats( trace_id=body['trace_id'],
        message_code=body['code'], 
        message=body['msg_text'])

    session.add(event_record)
    session.commit()
    session.close()

    logger.debug(f"stored event add record {body['trace_id']} code {body['code']}")
    return NoContent, 201


def get_events_stats():
    DB_ENGINE = create_engine(f"sqlite:///{app_config['datastore']['filename']}")
    Base.metadata.create_all(DB_ENGINE)

    DB_SESSION = sessionmaker(bind=DB_ENGINE)
    session = DB_SESSION()

    results = session.query(EventStats.message_code, 
                     func.count(EventStats.trace_id)
                     ).group_by(EventStats.message_code).all()

    print(results)

    stats = {code: count for code, count in results}

    session.close()
    return stats, 200


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
            log_topic = client.topics[str.encode(app_config['events']['log_topic'])]

            #create a consumer on a consumer group that only reads new messages
            # (uncommitted messages) when the service restarts (i.e, it doesn't
            # read all the old messages from the history in the message queue)
            consumer = log_topic.get_simple_consumer(consumer_group=b'log_event_group',
                                                reset_offset_on_start=False,
                                                auto_offset_reset=OffsetType.LATEST)
            
            for msg in consumer:
                msg_str = msg.value.decode('utf-8')
                msg = json.loads(msg_str)
                logger.info("Message: %s" % msg)

                payload = msg['payload']

                if msg['code'] in ["0001", "0002", "0003", "0004"]:
                    add_event_stats(payload)
                    #add log if success or fail
                    logger.info(f"Added event with id {payload['trace_id']} message code {payload['code']}")
                else:
                    logger.error("Unknown event msg code: %s" % msg['code'])
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
app.add_api("openapi.yaml", base_path="/",strict_validation=True, validate_responses=True)
app.add_middleware( CORSMiddleware, 
                   position=MiddlewarePosition.BEFORE_EXCEPTION, 
                   allow_origins=["*"], 
                   allow_credentials=True, 
                   allow_methods=["*"], 
                   allow_headers=["*"], )

if __name__ == "__main__":
    if not os.path.exists("/data/event_stats.sqlite"):
        create_db()
    tl = Thread(target=process_messages, args=())
    tl.setDaemon(True)
    tl.start()
    app.run(host='0.0.0.0',port=8120)