FROM python:3.13-slim AS ha_wheel_builder

RUN apt update && apt install \
    -y --no-install-recommends \
    build-essential

WORKDIR /pip-build
RUN pip wheel homeassistant fnv-hash-fast


FROM python:3.13-slim

RUN pip install paho-mqtt certifi

RUN --mount=type=cache,from=ha_wheel_builder,source=/pip-build,target=/pip-build pip install --only-binary :all: /pip-build/*.whl

# Sigh, the __init__.py tries use API severs, we just want the data...
RUN rm /usr/local/lib/python3.13/site-packages/homeassistant/components/mqtt/__init__.py

COPY openevse_mqtt_ha_discovery.py /openevse_mqtt_ha_discovery.py

CMD ["/usr/local/bin/python", "/openevse_mqtt_ha_discovery.py"]
