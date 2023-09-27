from dotenv import load_dotenv
import os
from handler.batcher import BatcherHandler
from handler.scan_api import EthScan

BLOCKS_PER_HOUR = 60 * 60 // 12
BLOCKS_PER_DAY = BLOCKS_PER_HOUR * 24
BLOCKS_PER_MONTH = BLOCKS_PER_DAY * 30


def main():
    load_dotenv()
    etherscan_endpoint = os.environ.get("ETHERSCAN_API_KEY")
    l1_endpoint = os.environ.get("ETHEREUM_RPC_ENDPOINT")

    bh = BatcherHandler.from_json("./batchers.json")
    es = EthScan(etherscan_endpoint, l1_endpoint)

    latest_height = 18204706
    target_height = latest_height - BLOCKS_PER_MONTH
    print(">>> Investigate blocks from {} to {}".format(target_height, latest_height))

    bh.run(es, target_height)


def main_graph_from_tx():
    BatcherHandler.fetch_txs_and_gen_graph()


def main_without_scan():
    BatcherHandler.simulate_with_json()


def main_gen_plot_graph():
    BatcherHandler.gen_plot_graph()


if __name__ == "__main__":
    # main()
    # main_graph_from_tx()
    # main_without_scan()
    main_gen_plot_graph()
