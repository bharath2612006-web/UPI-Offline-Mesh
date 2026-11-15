from copy import deepcopy
from app.config import PACKET_TTL

class VirtualDevice:
    def __init__(self, device_id, has_internet=False):
        self.device_id = device_id
        self.has_internet = has_internet
        self.packets = {}

class MeshSimulatorService:
    def __init__(self):
        self.devices = {}

    def seed_devices(self):
        self.devices = {
            "phone-alice": VirtualDevice("phone-alice"),
            "phone-bob": VirtualDevice("phone-bob"),
            "phone-stranger-1": VirtualDevice("phone-stranger-1"),
            "phone-stranger-2": VirtualDevice("phone-stranger-2"),
            "phone-bridge": VirtualDevice("phone-bridge", True),
        }

    def inject(self, packet):
        if "phone-alice" not in self.devices:
            self.seed_devices()
        self.devices["phone-alice"].packets[packet["packetId"]] = packet

    def gossip_round(self):
        snapshot = [(d.device_id, deepcopy(list(d.packets.values()))) for d in self.devices.values()]
        transfers = 0
        for source_id, packets in snapshot:
            for packet in packets:
                if packet["ttl"] <= 0:
                    continue
                forwarded = dict(packet)
                forwarded["ttl"] -= 1
                for target in self.devices.values():
                    if target.device_id != source_id and packet["packetId"] not in target.packets:
                        target.packets[packet["packetId"]] = forwarded
                        transfers += 1
        return {"transfers": transfers, "state": self.state()}

    def bridge_packets(self):
        out = []
        for device in self.devices.values():
            if device.has_internet:
                out.extend(device.packets.values())
        return out

    def state(self):
        return [{"deviceId": d.device_id, "hasInternet": d.has_internet,
                 "packetCount": len(d.packets), "packets": list(d.packets.values())}
                for d in self.devices.values()]

    def reset(self):
        self.seed_devices()
