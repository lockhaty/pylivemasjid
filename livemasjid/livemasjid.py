import logging
import requests
from threading import Thread
import paho.mqtt.client as mqtt

MQTT_URL = "livemasjid.com"
MQTT_PORT = 1883
MQTT_SSL_PORT = 8883
WEBSOCKET_PORT = 1884

STATUS_URL = "https://www.livemasjid.com/api/get_mountdetail_new.php"
log = logging.getLogger("pushbullet.Listener")


class Livemasjid(Thread):

    def __init__(self, subscriptions=None):
        Thread.__init__(self)
        self.client = mqtt.Client()
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.on_message_callback = None
        self.only_subscribed_streams = True
        self.subscriptions = []
        self.status = {}
        self.initial_load_count = 0
        self.update_status()
        self.set_subscriptions(subscriptions)

    def get_status(self):
        return self.status

    def update_status(self):
        request = requests.get(STATUS_URL)
        if request.status_code != 200:
            return

        status = request.json()
        mounts = status.get('mounts', [])

        new_status = {}

        for mount in mounts:

            source = {}
            sources = mount.get("ssources", [])
            if len(sources) > 0:
                source = sources[0]

            new_status[mount['mname']] = {
                "id": mount['mname'],
                "name": mount.get("sname"),
                "description": mount.get("sdesc"),
                "genre": mount.get("genre"),
                "status": "online" if mount.get("sstatus", "red") == 'green' else 'offline',
                "stream_url": source.get("url"),
                "stream_type": source.get("ctype"),
                "listeners": source.get("listeners", 0),
                "lat": mount.get("lat"),
                "lon": mount.get("lon"),
                "address": mount.get("location"),
                "website": mount.get("surl"),
                "pluscode": mount.get("pluscode")
            }
            self.status = new_status

    def set_subscriptions(self, subscriptions):
        if not subscriptions:
            subscriptions = []

        if type(subscriptions) != list:
            raise Exception("Expected a list of stream IDs")

        self.subscriptions = subscriptions

    def _on_connect(self, *_):
        def callback():
            self.client.subscribe('mounts/#')
        return callback()

    def _handle_user_callback(self, topic, msg):
        status = {}
        if topic in self.status:
            status = self.status[topic]

        self.on_message_callback(
            topic,
            msg.payload.decode('utf-8'),
            status
        )

    def _on_message(self, client, userdata, msg):
        def callback():
            if self.initial_load_count < len(self.status):
                self.initial_load_count += 1
            else:
                self.update_status()

            if not self.on_message_callback:
                return

            topic = msg.topic.replace('mounts/', "")

            if not self.only_subscribed_streams:
                return self._handle_user_callback(topic, msg)

            if topic not in self.subscriptions:
                return

            return self._handle_user_callback(topic, msg)

        return callback()

    def register_on_message_callback(self, callback, only_subscribed_streams=True):
        self.on_message_callback = callback
        self.only_subscribed_streams = only_subscribed_streams

    def run(self):
        self.client.connect(MQTT_URL, MQTT_PORT, 10)

        rc = 0
        while rc == 0:
            rc = self.client.loop_forever()
        return rc

