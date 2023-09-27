import json
from typing import List, Dict

from chainpy.eth.ethtype.hexbytes import EthAddress, EthHexBytes
from handler.scan_api import EthScan
from handler.utils import calc_gas_price_by_excess_blob_gas, calc_blobs_from_bytes
from matplotlib import pyplot as plt
import numpy as np

class Point:
    def __init__(self, height: int, blobs: int):
        self.height: int = height
        self.blobs: int = blobs


class Graph:
    def __init__(self, blobs: Dict[int, int]):
        self.blobs: Dict[int, int] = blobs  # height to accumulated blobs

    @classmethod
    def from_dict(cls, path: str = "./graph.json"):
        with open(path, "r") as f:
            blobs = json.load(f)
        return cls(blobs)

    @classmethod
    def from_points(cls, points: List[Point]):
        blobs = {}
        for point in points:
            stored_blobs = blobs.get(point.height)
            if stored_blobs is None:
                blobs[point.height] = point.blobs
            else:
                blobs[point.height] = stored_blobs + point.blobs
        return cls(blobs)

    def to_dict(self):
        sorted_blob = {}

        sorted_height = sorted(self.blobs.keys())
        for height in sorted_height:
            sorted_blob[height] = self.blobs[height]

        with open("graph.json", "w") as f:
            json.dump(sorted_blob, f)

    def simulate(self):
        excess_blob_gas = 0
        gas_per_blob = 2 ** 17

        domain = sorted(self.blobs.keys())
        for height in domain:
            blob_gas_price = calc_gas_price_by_excess_blob_gas(excess_blob_gas)
            print("blob_gas_price: {} in height({})".format(blob_gas_price, height))
            if blob_gas_price > 1:
                print("excess gas price more than 1: height({})".format(height))
                with open("singularity.json", "r") as f:
                    singularity = json.load(f)
                singularity[height] = blob_gas_price
                with open("singularity.json", "w") as f:
                    json.dump(singularity, f, indent=4)

            if self.blobs[height] > 3:
                excess_blob_gas += (self.blobs[height] - 3) * gas_per_blob
            elif self.blobs[height] < 3:
                excess_blob_gas -= (3 - self.blobs[height]) * gas_per_blob
                excess_blob_gas = max(0, excess_blob_gas)
            else:
                continue


class Batcher:
    def __init__(self, proj_name: str, batcher_addr: EthAddress, box_addr: EthAddress, func_selector: EthHexBytes):
        self.proj_name = proj_name
        self.batcher_addr = batcher_addr
        self.box_addr = box_addr
        self.func_selector = func_selector


class BatcherHandler:
    def __init__(self, batchers: Dict[str, Batcher]):
        self.batchers = batchers
        self.batcher_addresses = [batcher.batcher_addr for batcher in batchers.values()]

    @classmethod
    def from_json(cls, json_path: str):
        with open(json_path, "r") as f:
            batcher_json = json.load(f)

        batchers = dict()
        for batcher_info in batcher_json["batchers"]:
            batcher = Batcher(
                batcher_info["project_name"],
                EthAddress(batcher_info["batcher_addr"]),
                EthAddress(batcher_info["box_addr"]),
                EthHexBytes(batcher_info.get("func_selector"))
            )
            batchers[batcher.batcher_addr.hex()] = batcher
        return cls(batchers)

    def get_all_batcher_addrs(self) -> List[EthAddress]:
        return self.batcher_addresses

    def get_batcher_by_addr(self, addr: EthAddress) -> Batcher:
        return self.batchers.get(addr.hex())

    def get_box_addr_of_bather(self, batcher_addr: EthAddress) -> EthAddress:
        batcher = self.get_batcher_by_addr(batcher_addr)
        return batcher.box_addr

    def run(self, scan: EthScan, target_height: int):
        points = []
        for batcher in self.batchers.values():
            print(">>> Scanning for \"{}\" with addr {}".format(batcher.proj_name, batcher.batcher_addr.hex()))
            txs = scan.get_txs_after(target_height, batcher.batcher_addr)
            txs.reverse()  # older first
            with open("./batch_txs/{}.json".format(batcher.proj_name), "w") as f:
                json.dump({"txs": txs}, f)

            # logging
            start_height, end_height = txs[0]["blockNumber"], txs[-1]["blockNumber"]
            print("- Summary -> fetched {} txs from {} to {}".format(len(txs), start_height, end_height))

            for tx in txs:
                if EthAddress(tx["to"]) != batcher.box_addr:
                    continue
                data = EthHexBytes(tx["input"])
                if batcher.func_selector and data[:4].hex() != batcher.func_selector.hex():
                    continue

                blobs = calc_blobs_from_bytes(data)
                points.append(Point(tx["blockNumber"], blobs))

        graph = Graph.from_points(points)
        graph.to_dict()

    @staticmethod
    def fetch_txs_and_gen_graph():
        with open("./batchers.json", "r") as f:
            batcher_info = json.load(f)["batchers"]

        points = []
        for info in batcher_info:
            project_name = info["project_name"]
            print(">> Load {}'s txs".format(project_name))
            with open("./batch_txs/{}.json".format(project_name), "r") as f:
                txs = json.load(f)["txs"]
                for tx in txs:
                    blobs = calc_blobs_from_bytes(tx["input"])
                    points.append(Point(tx["blockNumber"], blobs))
        graph = Graph.from_points(points)
        graph.to_dict()
        print(">> Exported \"graph.json\" ")

    @staticmethod
    def simulate_with_json():
        graph = Graph.from_dict()
        graph.simulate()

    @staticmethod
    def gen_plot_graph():
        with open("singularity.json", "r") as f:
            singularity = json.load(f)

        domain = list(singularity.keys())  # height
        values = list(singularity.values())  # gas price

        plt.plot(domain, values, "k")
        plt.show()

        max_value = max(values)
        average_value = sum(values) / len(values)
        print("max: {}".format(max_value))
        print("avg: {}".format(average_value))
