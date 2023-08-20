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

# Sigh, the __init__.py tries use API severs, we just want the data...
RUN rm /usr/local/lib/python3.10/site-packages/homeassistant/components/mqtt/__init__.py

COPY openevse_mqtt_ha_discovery.py /openevse_mqtt_ha_discovery.py

CMD ["/usr/local/bin/python", "/openevse_mqtt_ha_discovery.py"]
