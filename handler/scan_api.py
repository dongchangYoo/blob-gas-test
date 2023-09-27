import requests
from chainpy.eth.ethtype.hexbytes import EthAddress

ETHERSCAN_BASE_URL = "https://api.etherscan.io/api"


class EthScan:
    def __init__(self, api_key: str, endpoint_url: str):
        self.api_key = api_key
        self.endpoint_url = endpoint_url

    def _build_url(self, module: str, action: str, params: dict = {}):
        url = "{}?module={}&action={}".format(ETHERSCAN_BASE_URL, module, action)
        for key, value in params.items():
            url += "&{}={}".format(key, value)
        url += "&apikey={}".format(self.api_key)
        return url

    def get_latest_height(self) -> int:
        body = {
            "jsonrpc": "2.0",
            "method": "eth_blockNumber",
            "params": [],
            "id": 1
        }
        headers = {"Content-type": "application/json"}
        result = requests.post(self.endpoint_url, json=body, headers=headers).json()["result"]
        return int(result, 16)

    def get_balance(self, addr: EthAddress) -> int:
        module, action, tag = "account", "balance", "latest"
        url = self._build_url(module, action, {"address": addr.hex(), "tag": "latest"})
        return int(requests.get(url).json()["result"])

    def get_txs_of(self, addr: EthAddress, end_height: int, total_tx_num: int = 1000):
        module, action = "account", "txlist"
        params = {
            "address": addr.hex(),
            "startblock": 0,
            "endblock": end_height,
            "page": 1,
            "offset": total_tx_num,
            "sort": "desc"  # from the latest one
        }
        url = self._build_url(module, action, params)
        json_resp = requests.get(url).json()
        result = json_resp["result"]

        min_height = result[-1]["blockNumber"] if len(result) != 0 else 0
        max_height = result[0]["blockNumber"] if len(result) != 0 else 0

        print("- fetched {} tx from {} to {}".format(len(result), min_height, max_height))
        return result

    def get_txs_after(self, target_height: int, addr: EthAddress):
        txs = []
        end_height = 99999999
        while True:
            result = self.get_txs_of(addr, end_height)
            if len(result) == 0:
                return txs

            front_height = int(result[0]["blockNumber"])
            if target_height >= front_height:
                return txs

            rear_height = int(result[-1]["blockNumber"])
            if rear_height == target_height:
                txs += result
                return txs

            if rear_height > target_height:
                txs += result
                end_height = int(txs[-1]["blockNumber"]) - 1
                continue

            if rear_height < target_height:
                front_idx = 1
                rear_idx = len(result) - 1
                middle_idx = (1 + len(result) - 1) // 2
                while True:
                    middle_height = int(result[middle_idx]["blockNumber"])
                    if rear_idx - front_idx < 1:
                        break
                    if middle_height > target_height:
                        # print("target: {}, middle: {}".format(target_height, middle_height))
                        # print("front: {}, middle: {}, rear: {}".format(front_idx, middle_idx, rear_idx))
                        front_idx = middle_idx + 1
                        middle_idx = (middle_idx + rear_idx) // 2
                    elif middle_height < target_height:
                        # print("target: {}, middle: {}".format(target_height, middle_height))
                        # print("front: {}, middle: {}, rear: {}".format(front_idx, middle_idx, rear_idx))
                        rear_idx = middle_idx - 1
                        middle_idx = (middle_idx + front_idx) // 2
                    else:
                        break
                txs += result[:middle_idx + 1]
                return txs
