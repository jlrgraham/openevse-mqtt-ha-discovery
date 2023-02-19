FROM python:3.10-slim AS ha_wheel_builder

RUN apt update && apt install \
    -y --no-install-recommends \
    build-essential

RUN pip wheel homeassistant


FROM python:3.10-slim

RUN pip install paho-mqtt certifi

COPY --from=ha_wheel_builder /homeassistant-*.whl /
COPY --from=ha_wheel_builder /ciso8601-*.whl /
RUN pip install /homeassistant-*.whl /ciso8601-*.whl numpy

COPY openevse_mqtt_ha_discovery.py /openevse_mqtt_ha_discovery.py

CMD ["/usr/local/bin/python", "/openevse_mqtt_ha_discovery.py"]
