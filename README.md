# openevse-mqtt-ha-discovery

Respond to OpenEVSE data published to an MQTT broker and create the corresponding [Home Assistant](https://www.home-assistant.io/) via [MQTT Discovery](https://www.home-assistant.io/docs/mqtt/discovery/) entries.

## Usage

### Kubernetes StatefulSet

    ---
    apiVersion: apps/v1
    kind: StatefulSet
    metadata:
      name: openevse-mqtt-ha-discovery
    spec:
      selector:
        matchLabels:
          app: openevse-mqtt-ha-discovery
      replicas: 1
      template:
        metadata:
          labels:
            app: openevse-mqtt-ha-discovery
        spec:
          terminationGracePeriodSeconds: 0
          containers:
          - env:
            - name: MQTT_BROKER
              value: mqtt.broker.name.com
            - name: MQTT_USERNAME
              value: mqtt_user
            - name: MQTT_PASSWORD
              value: itsasecret
            - name: HA_DISCOVERY_PREFIX
              value: ha-discovery
            image: jlrgraham/openevse-mqtt-ha-discovery:latest
            imagePullPolicy: Always
            name: openevse-mqtt-ha-discovery
          restartPolicy: Always

## Settings

All settings are taken from environmental variables at runtime.

| Variable | Description | Default |
| -------- | ----------- | ------- |
| `OPENEVSE_ANNOUNCE_MQTT_PREFIX` | The prefix under which OpenEVSE device(s) publish data. | `openevse/announce` |
| `MQTT_BROKER` | The hostname or IP of the MQTT broker. | `mqtt` |
| `MQTT_PORT` | The connection port on the MQTT broker.  If set to 8883 TLS is automatically used. | 8883 |
| `MQTT_CLIENT_ID` | The client name given to the MQTT broker.  See MQTT Connections for more details. | `openevse-mqtt-ha-discovery ` |
| `MQTT_USERNAME` | The username for the MQTT broker. | `None` |
| `MQTT_PASSWORD` | The password for the MQTT broker. | `None` |
| `HA_DISCOVERY_PREFIX` | The configured Home Assistant discovery prefix. | `homeassistant` |


### MQTT Connections

#### Authentication

Authentication will be attempted only if both `MQTT_USERNAME` and `MQTT_PASSWORD` are supplied.

#### Client ID

The MQTT client ID can be configured with the `MQTT_CLIENT_ID` variable.  This should generally be fixed for a given deployment.

#### TLS

If the MQTT broker port configuration is set to 8883 then the connector will automatically attempt to enable TLS for the connection to the broker.  The standard [Python certifi package](https://pypi.org/project/certifi/) will be used for CA roots, so public certs (ie: Let's Encrypt + others) should just work.

### MQTT Topics

There are two topic configuration controls: `OPENEVSE_ANNOUNCE_MQTT_PREFIX` and `HA_DISCOVERY_PREFIX`.

The `OPENEVSE_ANNOUNCE_MQTT_PREFIX` setting will control the top level prefix in MQTT used for OpenEVSE data.  This will result in a subscription to `<OPENEVSE_ANNOUNCE_MQTT_PREFIX>/+` (looking for published events of the form `openevse/announce/abcd` where `abcd` is the truncaed OpenEVSE device ID).

**NB:** To accomodate multiple OpenEVSE devices, the MQTT "Base-topic" setting *on the OpenEVSE* should be set to something like `openevse/openevse-abcd`. 

The `HA_DISCOVERY_PREFIX` setting should match [discovery prefix setting](https://www.home-assistant.io/docs/mqtt/discovery/#discovery_prefix) in Home Assistant.

## DockerHub Image

This script is available in a Docker image from: [https://hub.docker.com/repository/docker/jlrgraham/openevse-mqtt-ha-discovery/](https://hub.docker.com/repository/docker/jlrgraham/openevse-mqtt-ha-discovery/)
