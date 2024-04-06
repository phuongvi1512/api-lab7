import datetime, json, os
import logging.config
import swagger_ui_bundle
import yaml
from threading import Thread
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

#connect to database mysql
with open('app_conf.yml', 'r') as f: 
    app_config = yaml.safe_load(f.read())


# open logging file External Logging Configuration
with open('log_conf.yml', 'r') as f: 
    log_config = yaml.safe_load(f.read()) 
    logging.config.dictConfig(log_config)
logger = logging.getLogger('basicLogger')

logger.info("App Conf file: %s" % app_conf_file)
logger.info("Log Conf file: %s" % log_conf_file)

def get_config_file(index):
    """ get config file reading"""
    hostname = "%s:%d"%(app_config['events']['hostname'],
                        app_config['events']['port'])
    client = KafkaClient(hosts=hostname)
    topic = client.topics[str.encode(app_config['events']['topic'])]
    #reset offset on start so retrieve messages at beginning of the message queue
    #set timeout to 100ms
    consumer = topic.get_simple_consumer(reset_offset_on_start=True,
                                         consumer_timeout_ms=1000)
    logger.info("Retrieving config file reading at index %d" % index)
    try:
        idx = 0
        for msg in consumer:
            msg_str = msg.value.decode('utf-8')
            msg = json.loads(msg_str)
            if msg['type'] == 'configuration_file':
                idx += 1
            if idx == index:
                return msg['payload'], 200
    except:
        logger.error("No more message found")
    logger.error(" could not find config file reading at index %d" % index)

    return { "message": "Not found "}, 404 
def get_switch_report(index):
    """ get switch report reading"""
    hostname = "%s:%d"%(app_config['events']['hostname'],
                        app_config['events']['port'])
    client = KafkaClient(hosts=hostname)
    topic = client.topics[str.encode(app_config['events']['topic'])]
    #reset offset on start so retrieve messages at beginning of the message queue
    #set timeout to 100ms
    consumer = topic.get_simple_consumer(reset_offset_on_start=True,
                                         consumer_timeout_ms=1000)
    logger.info("Retrieving switch report reading at index %d" % index)
    try:
        idx = 0
        for msg in consumer:
            msg_str = msg.value.decode('utf-8')
            msg = json.loads(msg_str)
            if msg['type'] == 'switch_report':
                idx += 1
            if idx == index:
                return msg['payload'], 200
        
    except:
        logger.error("No more message found")
    logger.error(" could not find switch report reading at index %d" % index)
    return { "message": "Not found "}, 404

app = connexion.FlaskApp(__name__, specification_dir='')
app.add_api("openapi.yaml", strict_validation=True, validate_responses=True)
app.add_middleware( CORSMiddleware, 
                   position=MiddlewarePosition.BEFORE_EXCEPTION, 
                   allow_origins=["*"], 
                   allow_credentials=True, 
                   allow_methods=["*"], 
                   allow_headers=["*"], )

if __name__ == "__main__":
    tl = Thread(target=get_config_file)
    tl1 = Thread(target=get_switch_report)
    tl.setDaemon(True)
    tl.start()
    tl1.setDaemon(True)
    tl1.start()
    app.run(host='0.0.0.0',port=8110)
