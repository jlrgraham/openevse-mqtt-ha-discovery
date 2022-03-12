import paho.mqtt.client as mqtt
import certifi
import os
import time
import json
import logging


logger = logging.getLogger(__name__)
log_handler = logging.StreamHandler()
log_formatter = logging.Formatter('%(asctime)s [%(name)-12s] %(levelname)-8s %(message)s')
log_handler.setFormatter(log_formatter)
logger.addHandler(log_handler)
logger.setLevel(logging.INFO)


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
        "ha_device_class": "current",
        "ha_unit_of_meas": "A",
        "ha_stat_cla": "measurement",
        "ha_val_tpl": "{{ value | float / 1000 | round(2) }}",
    },
    "pilot": {
        "ha_domain": "sensor",
        "ha_name": "Pilot Current",
        "ha_device_class": "current",
        "ha_unit_of_meas": "A",
        "ha_stat_cla": "measurement",
        "ha_default_enabled": "false",
    },
    "session_energy": {
        "ha_domain": "sensor",
        "ha_name": "Session Energy",
        "ha_device_class": "power",
        "ha_unit_of_meas": "kW",
        "ha_stat_cla": "measurement",
        "ha_val_tpl": "{{ value | float / 1000 | round(2) }}",
        "ha_default_enabled": "false",
    },
    "state": {
        "ha_domain": "sensor",
        "ha_name": "State",
        "ha_val_tpl": "{% set state_map = {1: 'Ready', 2: 'Connected', 3: 'Charging', 4: 'Error'} %}{{ state_map[int(value)] }}",
    },
    "temp": {
        "ha_domain": "sensor",
        "ha_name": "Temp",
        "ha_device_class": "temperature",
        "ha_unit_of_meas": "°C",
        "ha_stat_cla": "measurement",
        "ha_val_tpl": "{{ value | float / 10 | round(2) }}",
    },
    "total_energy": {
        "ha_domain": "sensor",
        "ha_name": "Total Energy",
        "ha_device_class": "power",
        "ha_unit_of_meas": "kW",
        "ha_stat_cla": "measurement",
        "ha_val_tpl": "{{ value | float | round(2) }}",
        "ha_default_enabled": "false",
    },
    "voltage": {
        "ha_domain": "sensor",
        "ha_name": "Voltage",
        "ha_device_class": "voltage",
        "ha_unit_of_meas": "V",
        "ha_stat_cla": "measurement",
        "ha_default_enabled": "false",
    },
}


def publish_ha_discovery(client, announce_topic, announce_payload):
    topic_base = announce_payload["mqtt"]
    openevse_id = announce_payload["id"]

    for key, config in OPENEVSE_HA_DISCOVERY_KEYS.items():
        discovery_topic = f"{HA_DISCOVERY_PREFIX}/{config['ha_domain']}/openevse-{openevse_id}-{key}/config"

        discovery_data = {
            "~": topic_base,
            "name": f"OpenEVSE {openevse_id} {config['ha_name']}",
            "uniq_id": f"openevse-{openevse_id}-{key}",
            "stat_t": f"{topic_base}/{key}",
            "avty_t": announce_topic,
            "avty_tpl": '{{ value.find(\'"state":"connected"\') >= 0 }}',
            "pl_avail": "True",
            "pl_not_avail": "False",
            "dev": {
                "mf": "OpenEVSE LLC",
                "mdl": "OpenEVSE",
                #"sw": sensor_data["version"],
                "name": f"OpenEVSE {openevse_id}",
                "ids": [openevse_id],
                "cns": [
                    ["mac", openevse_id]
                ],
                "cu": announce_payload["http"],
            },
        }

        if "ha_device_class" in config.keys():
            discovery_data["dev_cla"] = config["ha_device_class"]
        if "ha_default_enabled" in config.keys():
            discovery_data["en"] = config["ha_default_enabled"]
        if "ha_unit_of_meas" in config.keys():
            discovery_data["unit_of_meas"] = config["ha_unit_of_meas"]
        if "ha_stat_cla" in config.keys():
            discovery_data["stat_cla"] = config["ha_stat_cla"]
        if "ha_val_tpl" in config.keys():
            discovery_data["val_tpl"] = config["ha_val_tpl"]

        (result, mid) = client.publish(discovery_topic, json.dumps(discovery_data))
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
