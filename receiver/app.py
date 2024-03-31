import connexion
from connexion import NoContent
from connexion.middleware import MiddlewarePosition
from starlette.middleware.cors import CORSMiddleware
from pykafka import KafkaClient
from pykafka.common import OffsetType
from datetime import datetime
import requests
import yaml, json
import logging, logging.config
import uuid
from time import sleep

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
    except Exception as e:
        logger.error(f"Connection failed the {retry_count + 1}th time")
        retry_count += 1
        #sleep for a number of seconds
        sleep(SLEEP_TIME)    
    


def add_switch_report(body):
    content = {
        "trace_id": f"{str(uuid.uuid4())}",
        "report_id": body["report_id"],
        "switch_id": body["switch_id"],
        "timestamp": f"{datetime.now()}",
        "status": body["status"],
        "temperature": body["temperature"]
    }


    # client = KafkaClient(hosts=f'{hostname}:{port}')
    # topic = client.topics[f'{topic_name}'.encode()]
    # producer = topic.get_sync_producer()
    msg = {
        "type": "switch_report",
        "datetime": datetime.now().strftime( "%Y-%m-%dT%H:%M:%S"),
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

    # client = KafkaClient(hosts=f'{hostname}:{port}')
    # topic = client.topics[f'{topic_name}'.encode()]
    # producer = topic.get_sync_producer()
    msg = {
        "type": "configuration_file",
        "datetime": datetime.now().strftime( "%Y-%m-%dT%H:%M:%S"),
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
