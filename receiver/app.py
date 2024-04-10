import json, os
import logging, logging.config
import uuid
from time import sleep
from datetime import datetime
import yaml
import connexion
from connexion import NoContent
from connexion.middleware import MiddlewarePosition
from starlette.middleware.cors import CORSMiddleware
from pykafka import KafkaClient
from pykafka.common import OffsetType

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

with open('app_conf.yml', 'r') as f: 
    app_config = yaml.safe_load(f.read())  
    hostname = app_config['events']['hostname']
    port = app_config['events']['port']
    topic_name = app_config['events']['topic']

#time to sleep and retry count
SLEEP_TIME = app_config['retry']['sleep_time']
MAX_RETRY_COUNT = app_config['retry']['max_count']

#logging
with open('log_conf.yml', 'r') as f: 
    log_config = yaml.safe_load(f.read()) 
    logging.config.dictConfig(log_config)

logger = logging.getLogger('basicLogger')

#connect to Kafka broker
retry_count = 0
hostname = "%s:%d"%(app_config['events']['hostname'], 
                    app_config['events']['port'])
while retry_count < MAX_RETRY_COUNT:
    #logging when trying to connect to Kafka
    logger.info(f"Trying to connect to Kafka {retry_count + 1}th time")
    try:
        client = KafkaClient(hosts=hostname)
        topic = client.topics[str.encode(app_config['events']['topic'])]
        producer = topic.get_sync_producer()
        
        #publish msg to event_log if successfully start and connect to Kafka
        #ready to receive msg on RESTful API
        log_topic = client.topics[str.encode(app_config['events']['log_topic'])]
        log_producer = log_topic.get_sync_producer()

        publish_event_logger()
        break
    except Exception as e:
        logger.error(f"Connection failed the {retry_count + 1}th time, error is {e}")
        #sleep for a number of seconds
        sleep(SLEEP_TIME)    
        retry_count += 1  

def publish_event_logger():
    content = {
        "trace_id": f"{str(uuid.uuid4())}",
        "timestamp": f"{datetime.now()}",
    }
    msg = {
        "code": "0001",
        "datetime": f"{datetime.now().strftime( "%Y-%m-%dT%H:%M:%S")}",
        "msg_text": "Code 0001. Successfully start and connect to Kafka. Ready to receive message",
        "payload": content
    }
    msg_str = json.dumps(msg)
    log_producer.produce(str.encode(msg_str))

def add_switch_report(body):
    content = {
        "trace_id": f"{str(uuid.uuid4())}",
        "report_id": body["report_id"],
        "switch_id": body["switch_id"],
        "timestamp": f"{datetime.now()}",
        "status": body["status"],
        "temperature": body["temperature"]
    }

    msg = {
        "type": "switch_report",
        "datetime": f"{datetime.now().strftime( "%Y-%m-%dT%H:%M:%S")}",
        "payload": content
    }
    msg_str = json.dumps(msg)
    producer.produce(str.encode(msg_str))
    return NoContent, 201


def add_config_file(body):
    content = {
        "trace_id": f"{str(uuid.uuid4())}",
        "file_id": body["file_id"],
        "switch_id": body["switch_id"],
        "timestamp": f"{datetime.now()}",
        "file_size": body["file_size"]
    }

    msg = {
        "type": "configuration_file",
        "datetime": f"{datetime.now().strftime( "%Y-%m-%dT%H:%M:%S")}",
        "payload": content
    }
    msg_str = json.dumps(msg)
    producer.produce(str.encode(msg_str))
    return NoContent, 201

# Your functions here to handle your endpoints
app = connexion.FlaskApp(__name__, specification_dir='')
app.add_api("openapi.yaml", 
            strict_validation=True,
            validate_responses=True)
app.add_middleware( CORSMiddleware, 
                   position=MiddlewarePosition.BEFORE_EXCEPTION, 
                   allow_origins=["*"], 
                   allow_credentials=True, 
                   allow_methods=["*"], 
                   allow_headers=["*"], )

if __name__ == "__main__":
    app.run(host='0.0.0.0',port=8080)
