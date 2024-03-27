import connexion
from connexion import NoContent
from connexion.middleware import MiddlewarePosition
from starlette.middleware.cors import CORSMiddleware
from pykafka import KafkaClient
from datetime import datetime
import requests
import yaml, json
import logging, logging.config
import uuid

with open('app_conf.yml', 'r') as f: 
    app_config = yaml.safe_load(f.read())  
    hostname = app_config['events']['hostname']
    port = app_config['events']['port']
    topic_name = app_config['events']['topic']

#logging
with open('log_conf.yml', 'r') as f: 
    log_config = yaml.safe_load(f.read()) 
    logging.config.dictConfig(log_config)

logger = logging.getLogger('basicLogger')

def add_switch_report(body):
    content = {
        "trace_id": f"{str(uuid.uuid4())}",
        "report_id": body["report_id"],
        "switch_id": body["switch_id"],
        "timestamp": f"{datetime.now()}",
        "status": body["status"],
        "temperature": body["temperature"]
    }

    with open('app_conf.yml', 'r') as f: 
        app_config = yaml.safe_load(f.read())

    # Call the Data Storage Service to store the switch report
    # response = requests.post(
    #     app_config["storereport"]["url"],
    #     json=content,
    #     headers={"Content-Type": "application/json"}
    # )

    # logger.info(f"return event add report response {content['trace_id']} with status {response.status_code}")    
    # return NoContent, response.status_code
    client = KafkaClient(hosts=f'{hostname}:{port}')
    topic = client.topics[f'{topic_name}'.encode()]
    producer = topic.get_sync_producer()
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

 
    
    # Call the Data Storage Service to store the config file
    # response = requests.post(
    #     app_config["storecfile"]["url"],
    #     json=content,
    #     headers={"Content-Type": "application/json"}
    # )
    # #logging
    # logger.info(f"return event add config response {content['trace_id']} with status {response.status_code}")
    # return NoContent, response.status_code

    client = KafkaClient(hosts=f'{hostname}:{port}')
    topic = client.topics[f'{topic_name}'.encode()]
    producer = topic.get_sync_producer()
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
    app.run(port=8080)
