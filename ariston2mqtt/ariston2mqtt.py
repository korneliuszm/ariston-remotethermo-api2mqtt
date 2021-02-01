import os
import re
import sys
import logging
import configparser


#for Github purpose - a2m.comf is gitignored because contains sensitive data
if os.path.isfile("a2m.conf"):
    _CONFIG_FILE = "a2m.conf"
else:
    _CONFIG_FILE = "ariston2mqtt.conf"

_CONFIG = configparser.ConfigParser()
_CONFIG_CONNECTION  = "CONNECTION"
_CONFIG_ARISTON = "ARISTON"

_LOGGER = logging.getLogger(__name__)
_LEVEL_CRITICAL = "CRITICAL"
_LEVEL_ERROR = "ERROR"
_LEVEL_WARNING = "WARNING"
_LEVEL_INFO = "INFO"
_LEVEL_DEBUG = "DEBUG"
_LEVEL_NOTSET = "NOTSET"

_LOGGING_LEVELS = [
    _LEVEL_CRITICAL,
    _LEVEL_ERROR,
    _LEVEL_WARNING,
    _LEVEL_INFO,
    _LEVEL_DEBUG,
    _LEVEL_NOTSET
]
_REGEX = '^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w+$'



def check(email):
    return re.search(_REGEX,email)


try:
    with open(_CONFIG_FILE) as f:
        _CONFIG.read_file(f)
except Exception as e:
    print("Cannot load configuration from file %s: %s" % (_CONFIG_FILE, str(e)))
    sys.exit(2)

connection = _CONFIG[_CONFIG_CONNECTION]
ariston_details = _CONFIG[_CONFIG_ARISTON] 

ariston_user_name = ariston_details.get('AristonUserName')
ariston_password = ariston_details.get('AristonPassword')
ariston_store_file = ariston_details.get('AristonStoreFile', 'False')
ariston_store_folder = ariston_details.get('AristonStoreFolder','')
ariston_logging_level = ariston_details.get('AristonloggingLevel', _LEVEL_NOTSET)

if not check(ariston_user_name):
    raise Exception("Login must be an email")

if len(ariston_password) == 0:
    raise Exception("Password can't be empty")

if ariston_logging_level not in _LOGGING_LEVELS:
    raise Exception("Invalid logging_level")

"""
Logging settings
"""
_logging_level = logging.getLevelName(ariston_logging_level)
_LOGGER.setLevel(_logging_level)
_console_handler = logging.StreamHandler()
_console_handler.setLevel(_logging_level)
_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
_console_handler.setFormatter(_formatter)
_LOGGER.addHandler(_console_handler)

_LOGGER.info("Config successfully read from %s", _CONFIG_FILE)



mqtt_broker = connection.get('MqttBroker', 'localhost')
mqtt_topic_prefix = connection.get('MqttTopicPrefix', 'ariston/')
mqtt_request_topic = connection.get('MqttRequestTopic', 'request')
mqtt_qos = connection.get('MqttQos', 0)
mqtt_retain = connection.get('MqttRetain', False)






#print(ariston_user_name)


#for key in connection:
#    print(key)

#print(config['CONNECTION']['MqttBroker'])





########################
#print(os.path.dirname(os.path.abspath(__file__)))
#print(os.path.abspath(os.getcwd()))