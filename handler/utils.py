from chainpy.eth.ethtype.hexbytes import EthHexBytes


def calc_blobs_from_bytes(input_bytes: EthHexBytes) -> int:
    elements_num = len(input_bytes) // 31
    if elements_num % 31 != 0:
        elements_num += 1
    blobs_num = elements_num // 4096
    if elements_num % 4096 != 0:
        blobs_num += 1

    return blobs_num


def fake_exponential(factor: int, numerator: int, denominator: int) -> int:
    i = 1
    output = 0
    numerator_accum = factor * denominator
    while numerator_accum > 0:
        output += numerator_accum
        numerator_accum = (numerator_accum * numerator) // (denominator * i)
        i += 1
    return output // denominator


def calc_gas_price_by_excess_blob_gas(excess_blob_gas: int) -> int:
    return fake_exponential(1, excess_blob_gas, 3338477)
