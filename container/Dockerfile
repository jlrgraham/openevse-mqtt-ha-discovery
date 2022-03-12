FROM python:3-slim

RUN pip install paho-mqtt certifi

COPY openevse_mqtt_ha_discovery.py /openevse_mqtt_ha_discovery.py

CMD ["/usr/local/bin/python", "/openevse_mqtt_ha_discovery.py"]
