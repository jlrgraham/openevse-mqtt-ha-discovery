import paho.mqtt.client as mqtt
import certifi
import os
import time
import json
import logging

from homeassistant.components.mqtt.abbreviations import ABBREVIATIONS as HA_MQTT_ABBREVIATIONS
from homeassistant.components.mqtt.abbreviations import DEVICE_ABBREVIATIONS as HA_MQTT_DEVICE_ABBREVIATIONS


logger = logging.getLogger(__name__)
log_handler = logging.StreamHandler()
log_formatter = logging.Formatter('%(asctime)s [%(name)-12s] %(levelname)-8s %(message)s')
log_handler.setFormatter(log_formatter)
logger.addHandler(log_handler)
logger.setLevel(logging.INFO)


HA_MQTT_TO_ABBREVIATIONS = {v: k for k, v in HA_MQTT_ABBREVIATIONS.items()}
HA_MQTT_TO_DEVICE_ABBREVIATIONS = {v: k for k, v in HA_MQTT_DEVICE_ABBREVIATIONS.items()}

def abbreviate_ha_mqtt_keys(data):
    def rendered_generator(data, parent_key=None):
        # Quick wrapper to ensure we don't get back a data structure with a bunch
        # of nested generators, doesn't easily seralize.
        if isinstance(data, dict):
            return dict(generator(data, parent_key=parent_key))
        else:
            return data

    def generator(data, parent_key=None):
        # Adjust which table we lookup in based on the parent_key, this should be the
        # key matching the data block we receive.  HA stores the "device" abbreviations
        # in a separate varible.
        lookup_table = HA_MQTT_TO_ABBREVIATIONS
        if parent_key is not None and parent_key == "device":
            lookup_table = HA_MQTT_TO_DEVICE_ABBREVIATIONS

        for key, value in data.items():
            logger.debug(f"abbreviate_ha_mqtt_keys generator: {key} -> {lookup_table.get(key, key)}")
            yield lookup_table.get(key, key), rendered_generator(value, parent_key=key)

    return rendered_generator(data)


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        logger.info("MQTT: Connected to broker.")
        announce_subscribe = f"{OPENEVSE_ANNOUNCE_MQTT_PREFIX}/+"
        logger.info(f"MQTT: Subscribe: {announce_subscribe}")
        client.subscribe(announce_subscribe)
    else:
        logger.error(f"MQTT: Failed to connect, rc: {rc}")


def on_message(client, userdata, msg):
    logger.debug(f"MQTT: Message received: f{str(msg.payload.decode('utf-8'))}")
    logger.debug(f"MQTT: Message topic: {msg.topic}, qos: {msg.qos}, retain flag: {msg.retain}")

    publish_ha_discovery(client, msg.topic, json.loads(msg.payload.decode("utf-8")))


OPENEVSE_ANNOUNCE_MQTT_PREFIX = os.getenv("OPENEVSE_ANNOUNCE_MQTT_PREFIX", "openevse/announce")

MQTT_BROKER = os.getenv("MQTT_BROKER", default="mqtt")
MQTT_PORT = os.getenv("MQTT_PORT", default=8883)
MQTT_CLIENT_ID = os.getenv("MQTT_CLIENT_ID", default=f"openevse-mqtt-ha-discovery")
MQTT_USERNAME = os.getenv("MQTT_USERNAME", default=None)
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD", default=None)

HA_DISCOVERY_PREFIX = os.getenv("HA_DISCOVERY_PREFIX", "homeassistant")


OPENEVSE_HA_DISCOVERY_KEYS = {
    "amp": {
        "ha_domain": "sensor",
        "ha_name": "Amps",
        "ha_discovery_config": {
            "device_class": "current",
            "unit_of_measurement": "A",
            "state_class": "measurement",
            "value_template": "{{ value | float / 1000 | round(2) }}",
        },
    },
    "pilot": {
        "ha_domain": "sensor",
        "ha_name": "Pilot Current",
        "ha_discovery_config": {
            "device_class": "current",
            "unit_of_measurement": "A",
            "state_class": "measurement",
            "enabled_by_default": "false",
        },
    },
    "session_energy": {
        "ha_domain": "sensor",
        "ha_name": "Session Energy",
        "ha_discovery_config": {
            "device_class": "power",
            "unit_of_measurement": "kW",
            "state_class": "measurement",
            "value_template": "{{ '%0.3f' | format((float(value) / 1000)) }}",
            "enabled_by_default": "false",
        },
    },
    "state": {
        "ha_domain": "sensor",
        "ha_name": "State",
        "ha_discovery_config": {
            "value_template": "{% set state_map = {1: 'Ready', 2: 'Connected', 3: 'Charging', 4: 'Error'} %}{{ state_map.get(int(value), 'Unknown') }}",
        },
    },
    "temp": {
        "ha_domain": "sensor",
        "ha_name": "Temp",
        "ha_discovery_config": {
            "device_class": "temperature",
            "unit_of_measurement": "°C",
            "state_class": "measurement",
            "value_template": "{{ value | float / 10 | round(2) }}",
        },
    },
    "total_energy": {
        "ha_domain": "sensor",
        "ha_name": "Total Energy",
        "ha_discovery_config": {
            "device_class": "power",
            "unit_of_measurement": "kW",
            "state_class": "measurement",
            "value_template": "{{ value | float | round(2) }}",
            "enabled_by_default": "false",
        },
    },
    "voltage": {
        "ha_domain": "sensor",
        "ha_name": "Voltage",
        "ha_discovery_config": {
            "device_class": "voltage",
            "unit_of_measurement": "V",
            "state_class": "measurement",
            "enabled_by_default": "false",
        },
    },
}


def publish_ha_discovery(client, announce_topic, announce_payload):
    if "mqtt" not in announce_payload:
        logger.error(f"Required key 'mqtt' not in: {announce_payload}")
        return

    topic_base = announce_payload["mqtt"]
    openevse_id = announce_payload["id"]

    for key, config in OPENEVSE_HA_DISCOVERY_KEYS.items():
        discovery_topic = f"{HA_DISCOVERY_PREFIX}/{config['ha_domain']}/openevse-{openevse_id}-{key}/config"

        discovery_data = {
            "~": topic_base,
            "name": f"OpenEVSE {openevse_id} {config['ha_name']}",
            "unique_id": f"openevse-{openevse_id}-{key}",
            "state_topic": f"{topic_base}/{key}",
            "availability_topic": announce_topic,
            "availability_template": '{{ value.find(\'"state":"connected"\') >= 0 }}',
            "payload_available": "True",
            "payload_not_available": "False",
            "device": {
                "manufacturer": "OpenEVSE LLC",
                "model": "OpenEVSE",
                "name": f"OpenEVSE {openevse_id}",
                "ids": [openevse_id],
                "connections": [
                    ["mac", openevse_id]
                ],
                "configuration_url": announce_payload["http"],
            },
        }

        for discovery_key, value in config.get("ha_discovery_config", {}).items():
            discovery_data[discovery_key] = value

        abbreviated_discovery_data = abbreviate_ha_mqtt_keys(discovery_data)
        logger.debug(f"discovery_data: {json.dumps(discovery_data)}")
        logger.debug(f"abbreviated_discovery_data: {json.dumps(abbreviated_discovery_data)}")

        (result, mid) = client.publish(discovery_topic, json.dumps(discovery_data), retain=True)
        if result != 0:
            logger.error(f"MQTT: Error publishing discovery, result: {result}, topic: {discovery_topic}")
        else:
            logger.info(f"MQTT: Published discovery, topic: {discovery_topic}")


def run():
    if MQTT_BROKER is None:
        raise Exception("MQTT_BROKER must be defined.")

    client = mqtt.Client(MQTT_CLIENT_ID)

    if MQTT_USERNAME is not None and MQTT_PASSWORD is not None:
        logger.info(f"MQTT: Authentication enabled, connect as: {MQTT_USERNAME}")
        client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)

    client.on_connect = on_connect
    client.on_message = on_message

    if MQTT_PORT == 8883:
        logger.info("MQTT: Enable TLS.")
        client.tls_set(certifi.where())

    logger.info(f"MQTT: Connect to {MQTT_BROKER}:{MQTT_PORT} ({MQTT_CLIENT_ID})")
    client.connect(MQTT_BROKER, MQTT_PORT, 60)

    client.loop_forever()


if __name__ == "__main__":
    run()
