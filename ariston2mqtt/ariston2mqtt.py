import re
import sys
import logging
import configparser
import json
import paho.mqtt.client as paho
from datetime import datetime
from packaging import version
from aristonremotethermo.ariston import AristonHandler

_CONFIG_FILE = "ariston2mqtt.conf"
_CONFIG = configparser.ConfigParser()
_CONFIG_CONNECTION = "CONNECTION"
_CONFIG_PAYLOAD = "PAYLOAD"
_CONFIG_ARISTON = "ARISTON"
_CONFIG_SENSORS = "SENSORS"
_API_VERSION_REQUIRED = "1.0.30"

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

_SENSOR_INCLUDED = "True"
_SENSOR_EXLUDED = "False"
_SENSOR_SETTINGS_ALLOWED = [
    _SENSOR_INCLUDED,
    _SENSOR_EXLUDED
]

_SUPPORTED_SENSORS = {
    'ch_flame',
    'ch_comfort_temperature',
    'signal_strength',
    'cooling_last_30d_list',
    'heating_last_365d',
    'heating_last_24h_list',
    'cooling_last_30d',
    'ch_mode',
    'dhw_set_temperature',
    'ch_water_temperature',
    'units',
    'cooling_last_7d_list',
    'dhw_storage_temperature',
    'internet_weather',
    'cooling_last_24h',
    'dhw_thermal_cleanse_cycle',
    'heating_last_30d',
    'heat_pump',
    'ch_antifreeze_temperature',
    'account_dhw_gas',
    'ch_auto_function',
    'water_last_30d',
    'heating_last_24h',
    'cooling_last_24h_list',
    'holiday_mode',
    'outside_temperature',
    'water_last_365d',
    'errors_count',
    'dhw_economy_temperature',
    'gas_type',
    'dhw_comfort_function',
    'errors',
    'online_version',
    'ch_program',
    'water_last_7d',
    'dhw_thermal_cleanse_function',
    'dhw_mode',
    'water_last_24h',
    'mode',
    'update',
    'water_last_7d_list',
    'internet_time',
    'ch_pilot',
    'heating_last_7d_list',
    'cooling_last_7d',
    'ch_set_temperature',
    'heating_last_7d',
    'water_last_365d_list',
    'account_dhw_electricity',
    'flame',
    'water_last_30d_list',
    'water_last_24h_list',
    'account_ch_gas',
    'account_ch_electricity',
    'ch_detected_temperature',
    'dhw_flame',
    'dhw_program',
    'cooling_last_365d',
    'cooling_last_365d_list',
    'dhw_comfort_temperature',
    'heating_last_365d_list',
    'ch_economy_temperature',
    'electricity_cost',
    'gas_cost',
    'heating_last_30d_list'
}

_OUTPUT_TOPIC = "topic"
_OUTPUT_JSON = "JSON"
_OUTPUT_TYPES = [
    _OUTPUT_TOPIC,
    _OUTPUT_JSON
]

_VALUE = "value"
_UNITS = "units"
_REGEX = r'^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w+$'


def sensors_updated(upd_sensors, *args, **kwargs):
    """ Triggered by aristonremotethermo.ariston
        List of uppdated sensors is sent as paratmeter
        to create_payload and returned value is sent to
        MQTT broker

        Paramters:
        ----------
        upd_sensors : dict
            The list of updated sensors
    """
    try:
        message_payload = create_payload(
            upd_sensors, payload_output_type)

        if type(message_payload) is dict:
            for key, value in message_payload.items():
                mqttc.publish(key, value, int(mqtt_qos), mqtt_retain)
        else:
            key = mqtt_topic_prefix + "json"
            mqttc.publish(key, message_payload, int(mqtt_qos), mqtt_retain)

    except Exception as e:
        _LOGGER.error(e.__str__())

    _LOGGER.debug(f"Updated: {upd_sensors}")


def status_updated(upd_statuses, *args, **kwargs):
    """ Triggered by aristonremotethermo.ariston

        Paramters:
        ----------
        upd_statuses : dict
            The list of updated statuses
    """
    _LOGGER.debug(f"Updated: {upd_statuses}, %s")


def check_user_name(email):
    """ Checking if email is provided in proper format """
    return re.search(_REGEX, email)


def read_sensors(sensors) -> set:
    """ Checking sensors provided in config file

        Sensors not supported are skipped
    """
    valid_sensors = set()
    rs_sensors = sensors
    for key, value in rs_sensors.items():
        if key not in supported_sensors:
            _LOGGER.warning(
                f"Sensor {key} is not supported and will be skipped")
            continue
        if value not in _SENSOR_SETTINGS_ALLOWED:
            _LOGGER.warning(
                f"Wrong entry for sensor {key} - only True/False allowed")
            continue
        if value == _SENSOR_INCLUDED:
            valid_sensors.add(key)
    return valid_sensors


def create_payload(message, output_type):
    """ Creating MQTT payload

        Parameters
        ----------
        message : dict
            Dictionary with:
                key = sensor name
                value = sensor value

        output_type : str
            "topic" - 1 MQTT topic per sensor
            "JSON" - 1 MQTT topic as JSON with all sensors

        Below sensors are skipped:
        - marked as False in config file
        - with None value
    """

    msg_payload = {}
    _LOGGER.debug(f"Message: {message}")
    if output_type == 'topic':
        for key in sensors:
            if key not in message:
                continue
            payload_to_update = {}
            if message[key][_VALUE] is not None:
                if type(message[key][_VALUE]) is dict:
                    message2 = message[key][_VALUE]
                    for key2, value2 in message2.items():
                        item_topic = mqtt_topic_prefix + key + "/" + key2
                        item_payload = value2
                        payload_to_update = {(item_topic, item_payload)}
                        msg_payload.update(payload_to_update)
                        _LOGGER.debug(f"Payload to update: \
                            {payload_to_update}")
                else:
                    key = str(key).strip()
                    value = str(message[key][_VALUE]).strip()
                    if message[key][_UNITS] is None or not payload_send_units:
                        units = ""
                    else:
                        units = str(message[key][_UNITS]).strip()
                    item_topic = mqtt_topic_prefix + key
                    item_payload = value + units
                    payload_to_update = {(item_topic, item_payload)}
                    msg_payload.update(payload_to_update)
                    _LOGGER.debug(f"Payload to update: \
                        {payload_to_update}")
        item_topic = mqtt_topic_prefix + 'last_update'  # timestamp
        item_payload = datetime.now().isoformat()
        payload_to_update = {(item_topic, item_payload)}
        msg_payload.update(payload_to_update)
        return msg_payload
    elif output_type == 'JSON':
        output_json = {}
        for key in sensors:
            if key not in message:
                continue
            if message[key][_VALUE] is not None:
                if message[key][_UNITS] is None or not payload_send_units:
                    output_json[key] = message[key][_VALUE]
                else:
                    output_json[key] = message[key]
        output_json['last_update'] = datetime.now().isoformat()  # timestamp
        return json.dumps(output_json)


def on_message(client, userdata, message):
    _LOGGER.debug("Received message '" + str(message.payload) + "' on topic '"
                  + message.topic + "' with QoS " + str(message.qos))


def on_connect(client, userdata, flags, rc):
    _LOGGER.debug("Connection returned result: " + paho.connack_string(rc))
    mqtt_subscribe_topic = mqtt_request_topic + '#'
    _LOGGER.debug(
        "Connected to MQTT broker - subscription for " + mqtt_subscribe_topic)
    mqttc.subscribe(mqtt_subscribe_topic, int(mqtt_qos))


def on_disconnect(client, userdata, rc):
    if rc != 0:
        _LOGGER.debug("Unexpected disconnection.")
    else:
        _LOGGER.debug("MQTT disconnected")


try:
    with open(_CONFIG_FILE) as f:
        _CONFIG.read_file(f)
except Exception as e:
    print(f"Cannot load configuration from file {_CONFIG_FILE}: {str(e)}")
    sys.exit(2)

connection = _CONFIG[_CONFIG_CONNECTION]
payload = _CONFIG[_CONFIG_PAYLOAD]
ariston_details = _CONFIG[_CONFIG_ARISTON]
sensors = _CONFIG[_CONFIG_SENSORS]

# AristonAPI settings #
ariston_user_name = ariston_details.get('AristonUserName')
ariston_password = ariston_details.get('AristonPassword')
ariston_store_file = ariston_details.getboolean('AristonStoreFile', False)
ariston_store_folder = ariston_details.get('AristonStoreFolder', '')
ariston_logging_level = ariston_details.get(
    'AristonloggingLevel', _LEVEL_NOTSET)

if not check_user_name(ariston_user_name):
    raise Exception("Login must be an email")

if len(ariston_password) == 0:
    raise Exception("Password cannot be empty")

if ariston_logging_level not in _LOGGING_LEVELS:
    raise Exception("Invalid logging_level")

# MQTT transfer #
mqtt_broker = connection.get('MqttBroker', 'localhost')
mqtt_port = connection.get('MqttPort', '1883')
mqtt_clientid = connection.get('MqttClientid', 'ariston-1')
mqtt_topic_prefix = connection.get('MqttTopicPrefix', 'ariston/')
mqtt_clean_session = connection.getboolean('MqttCleanSession', 'False')
mqtt_request_topic = connection.get('MqttRequestTopic', 'request')
mqtt_qos = connection.get('MqttQos', 0)
mqtt_retain = connection.getboolean('MqttRetain', 'False')

# Payload settings ####
payload_output_type = payload.get('PayloadOutputType', 'JSON')
payload_send_units = payload.getboolean('PayloadSendUnits', True)

if payload_output_type not in _OUTPUT_TYPES:
    raise Exception("Invalid output type")

# Logging settings #
_logging_level = logging.getLevelName(ariston_logging_level)
_LOGGER.setLevel(_logging_level)
_console_handler = logging.StreamHandler()
_console_handler.setLevel(_logging_level)
_formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
_console_handler.setFormatter(_formatter)
_LOGGER.addHandler(_console_handler)
_LOGGER.info(f"Config successfully read from {_CONFIG_FILE}")


supported_sensors = _SUPPORTED_SENSORS
sensors = read_sensors(sensors)

# Initiate Ariston API #
ApiInstance = AristonHandler(
    username=ariston_user_name,
    password=ariston_password,
    store_file=ariston_store_file,
    store_folder=ariston_store_folder,
    logging_level=ariston_logging_level,
    sensors=list(sensors)
)


if version.parse(ApiInstance.version) < version.parse(_API_VERSION_REQUIRED):
    _LOGGER.error(f"API Version: {ApiInstance.version} - minimmum \
    {_API_VERSION_REQUIRED} is required")
    sys.exit(2)
else:
    _LOGGER.debug(f"API Version: {ApiInstance.version} - Required \
    version: {_API_VERSION_REQUIRED}")

ApiInstance.start()

ApiInstance.subscribe_sensors(sensors_updated)
ApiInstance.subscribe_statuses(status_updated)

# Initialise MQTT #
mqtt_request_topic = mqtt_topic_prefix + mqtt_request_topic + '/'
mqttc = paho.Client(mqtt_clientid, mqtt_clean_session)

mqttc.on_message = on_message
mqttc.on_connect = on_connect
mqttc.on_disconnect = on_disconnect

mqttc.will_set('clients/ariston', payload="CU soon!", qos=0, retain=False)

mqttc.connect(mqtt_broker, int(mqtt_port), 60)

mqttc.loop_start()
