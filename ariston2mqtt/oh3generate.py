import sys
import logging
import configparser
import json

_CONFIG_FILE = "ariston2mqtt.conf"
_CONFIG = configparser.ConfigParser()
_CONFIG_CONNECTION = "CONNECTION"
_CONFIG_PAYLOAD = "PAYLOAD"
_CONFIG_ARISTON = "ARISTON"
_CONFIG_SENSORS = "SENSORS"
_CONFIG_OPENHAB3 = "OPENHAB3"

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

_LABEL = "label"
_TYPE = "type"
_DESCRIPTION = "description"

_SENSOR_INCLUDED = "True"
_SENSOR_EXLUDED = "False"
_SENSOR_SETTINGS_ALLOWED = [
    _SENSOR_INCLUDED,
    _SENSOR_EXLUDED
]


def read_sensors(sensors) -> set:
    valid_sensors = set()
    rs_sensors = sensors
    for key, value in rs_sensors.items():
        if key not in supported_sensors:
            _LOGGER.warning(
                "Sensor %s is not supported and will be skipped", key)
            continue
        if value not in _SENSOR_SETTINGS_ALLOWED:
            _LOGGER.warning(
                "Wrong entry for sensor %s - only True/False allowed", key)
            continue
        if value == _SENSOR_INCLUDED:
            valid_sensors.add(key)
    return valid_sensors


def create_header():
    header = ''
    header = header + 'label: ' + oh3_label + '\n'
    header = header + 'thingTypeUID: ' + oh3_thing_type_UID + '\n'
    header = header + 'configuration: ' + '{' + '}' + '\n'
    header = header + 'bridgeUID: ' + oh3_bridge_UID + '\n'
    header = header + 'location: ' + oh3_location + '\n'
    header = header + 'channels: \n'
    return header


def create_channel(sensors):
    channel = ''
    for key in sensors:
        channel = channel + '  - id: ' + oh3_channel_prefix + key + '\n'
        channel = channel + '    channelTypeUID: ' + \
                            supported_sensors[key][_TYPE] + '\n'
        channel = channel + '    label: ' + \
                            supported_sensors[key][_LABEL] + '\n'
        channel = channel + '    description: ' + \
                            supported_sensors[key][_DESCRIPTION] + '\n'
        channel = channel + '    configuration:' + '\n'
        channel = channel + '      stateTopic: ' + \
                            mqtt_topic_prefix + key + '\n'
    return channel


def create_footer():
    channel = ''
    channel = channel + '  - id: ' + oh3_channel_prefix + 'last_update \n'
    channel = channel + '    channelTypeUID: mqtt:datetime\n'
    channel = channel + '    label: Last update \n'
    channel = channel + '    description: null \n'
    channel = channel + '    configuration:' + '\n'
    channel = channel + '      stateTopic: ' + \
                        mqtt_topic_prefix + 'last_update'
    return channel


try:
    with open(_CONFIG_FILE) as f:
        _CONFIG.read_file(f)
except Exception as e:
    print("Cannot load configuration from file %s: %s" %
          (_CONFIG_FILE, str(e)))
    sys.exit(2)

connection = _CONFIG[_CONFIG_CONNECTION]
ariston_details = _CONFIG[_CONFIG_ARISTON]
sensors = _CONFIG[_CONFIG_SENSORS]
openhab3 = _CONFIG[_CONFIG_OPENHAB3]

oh3_channel_prefix = openhab3.get('OH3ChannelPrefix', 'Ariston_')
oh3_label = openhab3.get('OH3Label', 'Ariston')
oh3_thing_type_UID = openhab3.get('OH3thingTypeUID', 'mqtt:topic')
oh3_bridge_UID = openhab3.get('OH3bridgeUID', 'mqtt:broker:mosquitto')
oh3_location = openhab3.get('OH3Location', 'Boiler')
oh3_output_file = openhab3.get('OH3OutputFile', 'ariston2mqtt.yaml')
oh3_sensors_file = openhab3.get('OH3SensorsFile', 'oh3sensors.json')

mqtt_topic_prefix = connection.get('MqttTopicPrefix', 'ariston/')

# Logging settings #
ariston_logging_level = ariston_details.get(
    'AristonloggingLevel', _LEVEL_NOTSET)

_logging_level = logging.getLevelName(ariston_logging_level)
_LOGGER.setLevel(_logging_level)
_console_handler = logging.StreamHandler()
_console_handler.setLevel(_logging_level)
_formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
_console_handler.setFormatter(_formatter)
_LOGGER.addHandler(_console_handler)
_LOGGER.info("Config successfully read from %s", _CONFIG_FILE)

try:
    with open(oh3_sensors_file) as f:
        supported_sensors = json.load(f)
except Exception as e:
    print("Cannot load configuration from file %s: %s" %
          (oh3_sensors_file, str(e)))
    sys.exit(2)

sensors = read_sensors(sensors)

try:
    with open(oh3_output_file, "w") as f:
        f.write(create_header())
        f.write(create_channel(sensors))
        f.write(create_footer())
        f.close()
except Exception as e:
    print("Cannot write to file %s: %s" %
          (oh3_output_file, str(e)))
    sys.exit(2)
