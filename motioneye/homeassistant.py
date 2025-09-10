# Copyright (c) 2024 Jules
# This file is part of motionEye.
#
# This module handles integration with Home Assistant via MQTT Discovery.

import json
import logging
import paho.mqtt.client as mqtt
import os
import time

from motioneye import settings

class HomeAssistantAgent:
    def __init__(self, main_config):
        self._mqtt_settings = main_config.get('@_mqtt', {})
        self._enabled = self._mqtt_settings.get('enabled', False)
        self._client = None

        if self._enabled:
            self.connect()

    def connect(self):
        if not self._enabled:
            return

        broker = self._mqtt_settings.get('broker_address')
        port = self._mqtt_settings.get('broker_port', 1883)
        username = self._mqtt_settings.get('username')
        password = self._mqtt_settings.get('password')
        enable_tls = self._mqtt_settings.get('enable_tls', False)
        ca_certs_path = self._mqtt_settings.get('ca_certs_path', None)

        if not broker:
            logging.warning('MQTT enabled but no broker address is configured.')
            self._enabled = False
            return

        logging.info(f'Connecting to MQTT broker at {broker}:{port}')
        self._client = mqtt.Client(client_id="motionEye_server")
        if username and password:
            self._client.username_pw_set(username, password)

        if enable_tls:
            logging.info("MQTT TLS is enabled.")
            try:
                # If a path is provided, use it. Otherwise, paho-mqtt will use system default CAs.
                self._client.tls_set(ca_certs=ca_certs_path if ca_certs_path else None)
            except Exception as e:
                logging.error(f"Failed to set MQTT TLS options: {e}")
                self._enabled = False
                return

        try:
            self._client.connect(broker, port, 60)
            self._client.loop_start()
            logging.info('MQTT client connected and loop started.')
        except Exception as e:
            logging.error(f'Failed to connect to MQTT broker: {e}')
            self._enabled = False
            self._client = None

    def publish_discovery_message(self, camera_config):
        if not self._enabled or not self._client:
            return

        camera_id = camera_config['@id']
        camera_name = camera_config['camera_name']

        device_info = {
            "identifiers": [f"motioneye_camera_{camera_id}"],
            "name": f"motionEye Camera - {camera_name}",
            "manufacturer": "motionEye Project",
            "model": "motionEye"
        }

        motion_sensor_topic = f"homeassistant/binary_sensor/motioneye_{camera_id}_motion/config"
        motion_state_topic = f"motioneye/camera_{camera_id}/motion"

        motion_payload = {
            "name": f"{camera_name} Motion",
            "device_class": "motion",
            "state_topic": motion_state_topic,
            "unique_id": f"motioneye_motionsensor_{camera_id}",
            "device": device_info
        }

        logging.info(f"Publishing discovery message for motion sensor of camera {camera_id}")
        self._client.publish(motion_sensor_topic, json.dumps(motion_payload), retain=True)

    def publish_motion_state(self, camera_id, motion_detected):
        if not self._enabled or not self._client:
            return

        motion_state_topic = f"motioneye/camera_{camera_id}/motion"
        payload = "ON" if motion_detected else "OFF"
        logging.info(f"Publishing motion state for camera {camera_id}: {payload}")
        self._client.publish(motion_state_topic, payload, retain=True)

    def disconnect(self):
        if self._client:
            self._client.loop_stop()
            self._client.disconnect()
            logging.info("MQTT client disconnected.")

# Global instance for the main server process
g_ha_agent = None

def init(main_config):
    global g_ha_agent
    if not g_ha_agent:
        g_ha_agent = HomeAssistantAgent(main_config)
    return g_ha_agent

def get_agent():
    return g_ha_agent


def mqtt_publish_main(parser, args):
    """The main function for the mqtt_publish meyectl command."""
    import argparse
    from motioneye import config

    parser.add_argument('topic', help='The sub-topic to publish to (e.g. motion_on)')
    parser.add_argument('camera_id', type=int, help='The ID of the camera')
    options = parser.parse_args(args)

    main_config = config.get_main()
    mqtt_settings = main_config.get('@_mqtt', {})

    if not mqtt_settings.get('enabled'):
        return

    broker = mqtt_settings.get('broker_address')
    port = mqtt_settings.get('broker_port', 1883)
    username = mqtt_settings.get('username')
    password = mqtt_settings.get('password')
    enable_tls = mqtt_settings.get('enable_tls', False)
    ca_certs_path = mqtt_settings.get('ca_certs_path', None)

    if not broker:
        logging.error('MQTT is enabled, but no broker address is configured.')
        return

    client = mqtt.Client(client_id=f"motionEye_publisher_{os.getpid()}")
    if username and password:
        client.username_pw_set(username, password)

    if enable_tls:
        try:
            client.tls_set(ca_certs=ca_certs_path if ca_certs_path else None)
        except Exception as e:
            logging.error(f"MQTT Publisher failed to set TLS options: {e}")
            return

    try:
        client.connect(broker, port, 60)
    except Exception as e:
        logging.error(f"MQTT publisher failed to connect: {e}")
        return

    camera_id = options.camera_id
    if options.topic == 'motion_on':
        state_topic = f"motioneye/camera_{camera_id}/motion"
        payload = "ON"
    elif options.topic == 'motion_off':
        state_topic = f"motioneye/camera_{camera_id}/motion"
        payload = "OFF"
    else:
        logging.error(f"Unknown MQTT topic '{options.topic}'")
        client.disconnect()
        return

    logging.info(f"MQTT Publisher: sending '{payload}' to '{state_topic}'")
    client.publish(state_topic, payload, retain=True)
    client.disconnect()
    logging.debug("MQTT Publisher: disconnected.")
