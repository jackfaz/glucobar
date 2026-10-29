import hashlib
import json
import socket
import socketserver
import threading
import time
import unittest
import urllib.error
import urllib.request
from unittest import mock

from glucobar import bridge, credentials
from glucobar.config import DEFAULT_CONFIG


def free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class FakeCtl:
    def __init__(self, **cfg):
        now = time.time()
        self.cfg = dict(DEFAULT_CONFIG, **cfg)
        self.history = [{"mgdl": 120 + i, "trend": "Flat", "time": now - (30 - 5 * i) * 60}
                        for i in range(6)]
        self.current = {"mgdl": 131, "trend": 4, "time": now - 60}
        self.history.append(self.current)
        self.others = [{"id": "p2", "label": "Luca",
                        "current": {"mgdl": 64, "trend": 2, "time": now - 120}}]
        self.error = None

    def person_key(self, pid=None):
        return pid or "p1"

    def person_label(self, pid=None):
        return "Anna"


class SnapshotTest(unittest.TestCase):
    def test_people(self):
        snap = bridge.make_snapshot(FakeCtl())
        anna, luca = snap["people"]
        self.assertEqual((anna["name"], anna["value"], anna["trend"], anna["arrow"]),
                         ("Anna", 131, "FortyFiveUp", "↗"))
        self.assertTrue(anna["primary"])
        self.assertEqual(anna["state"], "in_range")
        self.assertEqual(anna["age_minutes"], 1)
        self.assertEqual(len(anna["history"]), 7)
        self.assertEqual((luca["state"], luca["trend"]), ("low", "FortyFiveDown"))
        self.assertNotIn("history", luca)

    def test_mmol(self):
        snap = bridge.make_snapshot(FakeCtl(unit="mmol/L"))
        self.assertEqual(snap["people"][0]["value"], 7.3)
        self.assertEqual(bridge.nightscout_status(snap)["settings"]["units"], "mmol")


class HttpTest(unittest.TestCase):
    def start(self, **cfg):
        self.port = free_port()
        self.ctl = FakeCtl(bridge_http=True, bridge_port=self.port, **cfg)
        self.bridge = bridge.Bridge(self.ctl)
        self.addCleanup(self.bridge.stop)
        self.bridge.update()

    def get(self, path, headers=None):
        req = urllib.request.Request(f"http://127.0.0.1:{self.port}{path}", headers=headers or {})
        with urllib.request.urlopen(req, timeout=5) as r:
            body = r.read().decode()
            return json.loads(body) if r.headers["Content-Type"].startswith("application/json") \
                else body

    def test_endpoints(self):
        self.start()
        self.assertEqual(self.get("/api/v1/current")["value"], 131)
        self.assertEqual(self.get("/api/v1/current?person=luca")["value"], 64)
        self.assertEqual(self.get("/api/v1/current?person=1")["name"], "Luca")
        self.assertEqual([p["name"] for p in self.get("/api/v1/people")], ["Anna", "Luca"])
        self.assertEqual(len(self.get("/api/v1/history?hours=1")), 7)
        # come Nightscout: dalla lettura più recente, con freccia e delta solo sull'ultima
        entries = self.get("/api/v1/entries.json?count=3")
        self.assertEqual([e["sgv"] for e in entries], [131, 125, 124])
        self.assertEqual((entries[0]["direction"], entries[0]["type"]), ("FortyFiveUp", "sgv"))
        self.assertEqual(len(self.get("/api/v1/entries/current.json")), 1)
        status = self.get("/api/v1/status.json")
        self.assertEqual(status["settings"]["thresholds"]["bgTargetTop"], 180)
        self.assertIn("api/v1/current", self.get("/overlay?size=90"))
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            self.get("/nothing")
        self.assertEqual(ctx.exception.code, 404)

    def test_key(self):
        self.start(bridge_token="abc")
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            self.get("/api/v1/current")
        self.assertEqual(ctx.exception.code, 401)
        self.assertEqual(self.get("/api/v1/current?token=abc")["value"], 131)
        sha1 = hashlib.sha1(b"abc").hexdigest()        # come le app per Nightscout
        self.assertEqual(self.get("/api/v1/entries.json", {"api-secret": sha1})[0]["sgv"], 131)

    def test_only_this_computer_by_default(self):
        self.start()
        self.assertEqual(self.bridge.server.server_address[0], "127.0.0.1")
        self.assertEqual(self.bridge.addresses(), [f"http://127.0.0.1:{self.port}"])

    def test_port_in_use(self):
        with socket.socket() as busy:
            busy.bind(("127.0.0.1", 0))
            busy.listen()
            ctl = FakeCtl(bridge_http=True, bridge_port=busy.getsockname()[1])
            b = bridge.Bridge(ctl)
            self.assertIsNone(b.server)
            self.assertTrue(b.http_error)


class FakeBroker(socketserver.BaseRequestHandler):
    """Un broker MQTT minimo: accetta la connessione e annota i PUBLISH."""
    published = []
    connects = []

    def read_packet(self):
        head = self.request.recv(1)
        if not head:
            return None, b""
        length, shift = 0, 0
        while True:
            byte = self.request.recv(1)[0]
            length |= (byte & 0x7F) << shift
            shift += 7
            if not byte & 0x80:
                break
        data = b""
        while len(data) < length:
            data += self.request.recv(length - len(data))
        return head[0], data

    def handle(self):
        while True:
            kind, data = self.read_packet()
            if kind is None:
                return
            if kind >> 4 == 1:
                self.connects.append(data)
                self.request.sendall(b"\x20\x02\x00\x00")
            elif kind >> 4 == 3:
                size = int.from_bytes(data[:2], "big")
                self.published.append((data[2:2 + size].decode(), data[2 + size:].decode(),
                                       bool(kind & 1)))
            elif kind >> 4 == 14:
                return


class MqttTest(unittest.TestCase):
    def test_publishes_state_and_discovery(self):
        FakeBroker.published, FakeBroker.connects = [], []
        server = socketserver.ThreadingTCPServer(("127.0.0.1", 0), FakeBroker)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        self.addCleanup(server.shutdown)
        with mock.patch.object(credentials, "get_password", return_value="pw"):
            ctl = FakeCtl(mqtt=True, mqtt_host="127.0.0.1", mqtt_port=server.server_address[1],
                          mqtt_user="ha")
            b = bridge.Bridge(ctl)
            self.addCleanup(b.stop)
            b.update()
            deadline = time.time() + 10
            while time.time() < deadline and len(FakeBroker.published) < 5:
                time.sleep(0.1)
        topics = [topic for topic, _payload, _retain in FakeBroker.published]
        self.assertEqual(topics[0], "glucobar/status")
        self.assertIn("homeassistant/sensor/glucobar_p1/config", topics)
        self.assertIn("glucobar/p2/state", topics)
        state = dict((t, p) for t, p, _r in FakeBroker.published)["glucobar/p1/state"]
        self.assertEqual(json.loads(state)["value"], 131)
        config = json.loads(dict((t, p) for t, p, _r in FakeBroker.published)[
            "homeassistant/sensor/glucobar_p2/config"])
        self.assertEqual((config["name"], config["unit_of_measurement"]), ("Glucose Luca", "mg/dL"))
        self.assertTrue(all(retain for _t, _p, retain in FakeBroker.published))
        connect = FakeBroker.connects[0]
        self.assertIn(b"MQTT", connect)
        self.assertIn(b"ha", connect)
        self.assertIn(b"pw", connect)
        self.assertEqual(b.mqtt.status, "ok")


if __name__ == "__main__":
    unittest.main()
