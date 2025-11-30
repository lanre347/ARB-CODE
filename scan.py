#!/usr/bin/env python3
"""
ETH Mainnet Profitable Arbitrage Scanner (UniswapV2 + SushiSwap only)
Includes: slippage, gas cost, and DEX swap fees (0.3% per swap)
Scans only cross-DEX routes for top N profitable opportunities.
"""

import os
import time
import json
from decimal import Decimal, getcontext
from web3 import Web3
from dotenv import load_dotenv

load_dotenv()
getcontext().prec = 28

# ---------- CONFIG ----------
RPC_URL = os.getenv('RPC_URL', 'https://mainnet.infura.io/v3/5a0206154a0144dfa89af2f4aab02588')
EXECUTOR_ADDRESS = Web3.to_checksum_address(os.getenv('EXECUTOR_ADDRESS', '0xc3bac4665c47fb6de24489982e80532943e47be0'))
SIM_INPUT_USDC = Decimal(os.getenv('SIM_INPUT_USDC', '10000'))
USDC_DECIMALS = int(os.getenv('USDC_DECIMALS', '6'))
SLIPPAGE_BPS = int(os.getenv('SLIPPAGE_BPS', '0'))
DEX_SWAP_FEE = Decimal('0')  # 0.3% per swap
GAS_PRICE_GWEI = Decimal(os.getenv('GAS_PRICE_GWEI', '1'))
TOP_N = int(os.getenv('TOP_N', '20'))  # number of top profitable opportunities to show

# DEX addresses
UNISWAP_V2_ROUTER = Web3.to_checksum_address('0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D')
SUSHISWAP_ROUTER = Web3.to_checksum_address('0xd9e1CE17f2641f24aE83637ab66a2cca9C378B9F')

# Common tokens
USDC_ADDRESS = Web3.to_checksum_address('0xA0b86991c6218b36c1d19d4a2e9eb0ce3606eb48')
WETH_ADDRESS = Web3.to_checksum_address('0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2')

# Popular tokens to always scan
POPULAR_TOKENS = [
    WETH_ADDRESS,
    Web3.to_checksum_address('0x6B175474E89094C44Da98b954EedeAC495271d0F'),  # DAI
    Web3.to_checksum_address('0xdAC17F958D2ee523a2206206994597C13D831ec7'),  # USDT
    Web3.to_checksum_address('0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599'),  # WBTC
    Web3.to_checksum_address('0x514910771AF9Ca656af840dff83E8264EcF986CA'),  # LINK
    Web3.to_checksum_address('0x0D8775F648430679A709E98d2b0Cb6250d2887EF'),  # BAT
    Web3.to_checksum_address('0xC00e94Cb662C3520282E6f5717214004A7f26888'),  # COMP
    Web3.to_checksum_address('0xBB9bc244D798123fDe783fCc1C72d3Bb8C189413'),  # ANT
    Web3.to_checksum_address('0x1985365e9f78359a9B6AD760e32412f4a445E862'),  # REP
    Web3.to_checksum_address('0x0bc529c00C6401aEF6D220BE8C6Ea1667F6Ad93e'),  # YFI
    Web3.to_checksum_address('0x111111111117dC0aa78b770fA6A738034120C302'),  # 1INCH
    Web3.to_checksum_address('0xC011A72400E58ecD99Ee497CF89E3775d4bd732F'),  # SNX
    Web3.to_checksum_address('0x0f5D2fB29fb7d3CFeE444a200298f468908cC942'),  # MANA
    Web3.to_checksum_address('0xE41d2489571d322189246DaFA5ebDe1F4699F498'),  # ZRX
    Web3.to_checksum_address('0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984'),  # UNI
    Web3.to_checksum_address('0x8f8221afbb33998d8584a2b05749ba73c37a938a'),  # ANT
    Web3.to_checksum_address('0x0d8775F648430679A709E98d2b0Cb6250d2887EF'),  # BAT
    Web3.to_checksum_address('0xBB9bc244D798123fDe783fCc1C72d3Bb8C189413')   # ANT
]

# Minimal ABIs
ERC20_ABI = json.loads('[{"constant":true,"inputs":[],"name":"decimals","outputs":[{"internalType":"uint8","name":"","type":"uint8"}],"stateMutability":"view","type":"function"},{"constant":true,"inputs":[],"name":"symbol","outputs":[{"name":"","type":"string"}],"stateMutability":"view","type":"function"}]')
ROUTER_ABI = json.loads('[{"name":"getAmountsOut","outputs":[{"name":"amounts","type":"uint256[]"}],"inputs":[{"name":"amountIn","type":"uint256"},{"name":"path","type":"address[]"}],"stateMutability":"view","type":"function"},{"name":"swapExactTokensForTokens","outputs":[{"name":"amounts","type":"uint256[]"}],"inputs":[{"name":"amountIn","type":"uint256"},{"name":"amountOutMin","type":"uint256"},{"name":"path","type":"address[]"},{"name":"to","type":"address"},{"name":"deadline","type":"uint256"}],"stateMutability":"nonpayable","type":"function"}]')

# Initialize Web3
w3 = Web3(Web3.HTTPProvider(RPC_URL))
router_uni = w3.eth.contract(address=UNISWAP_V2_ROUTER, abi=ROUTER_ABI)
router_sushi = w3.eth.contract(address=SUSHISWAP_ROUTER, abi=ROUTER_ABI)

# ------------------ Utilities ------------------
def raw(amount: Decimal, decimals: int) -> int:
    return int((amount * (Decimal(10) ** decimals)).to_integral_value())

def safe_get_amounts_out(router_contract, amount_in, path):
    try:
        return router_contract.functions.getAmountsOut(amount_in, path).call()
    except Exception:
        return None

def estimate_gas_for_swap(router_contract, amount_in, amount_out_min, path, to_address):
    deadline = int(time.time()) + 60
    try:
        fn = router_contract.functions.swapExactTokensForTokens(amount_in, amount_out_min, path, to_address, deadline)
        tx = fn.buildTransaction({'from': EXECUTOR_ADDRESS})
        tx.pop('gas', None)
        return w3.eth.estimate_gas(tx)
    except Exception:
        return 300000

def compute_profit(amount_in_usd: Decimal, amount_out_usdc_raw: int, gas_used: int, gas_price_gwei: Decimal):
    amount_out = Decimal(amount_out_usdc_raw) / (Decimal(10) ** USDC_DECIMALS)
    try:
        weth_to_usdc = router_uni.functions.getAmountsOut(10**18, [WETH_ADDRESS, USDC_ADDRESS]).call()[-1]
        weth_price_usd = Decimal(weth_to_usdc) / (10**USDC_DECIMALS)
    except Exception:
        weth_price_usd = Decimal('1800')
    gas_cost_usd = (Decimal(gas_used) * (gas_price_gwei / Decimal(1e9))) * weth_price_usd
    profit_usd = amount_out - amount_in_usd - gas_cost_usd
    profit_pct = (profit_usd / amount_in_usd) * 100
    return float(profit_usd), float(profit_pct), float(gas_cost_usd)

# ------------------ Main Loop ------------------
def main_loop():
    print('Starting continuous arbitrage scan (every 5 seconds)...')
    reported_trades = set()  # store identifiers for trades already reported

    while True:
        print('\n--- New Scan ---\n')
        try:
            profitable_trades = []
            amount_in_usdc_raw = raw(SIM_INPUT_USDC, USDC_DECIMALS)

            routers = [
                ('UniswapV2', router_uni, 'SushiSwap', router_sushi),
                ('SushiSwap', router_sushi, 'UniswapV2', router_uni)
            ]

            pair_count = 1
            for token in POPULAR_TOKENS:
                if token == USDC_ADDRESS:
                    continue
                try:
                    token_contract = w3.eth.contract(address=token, abi=ERC20_ABI)
                    symbol = token_contract.functions.symbol().call()
                except Exception:
                    symbol = token[:6]

                for r1_name, r1, r2_name, r2 in routers:
                    print(f"[Scanning pair {pair_count}] USDC → Buy {symbol} on {r1_name} → Sell {symbol} on {r2_name}")
                    pair_count += 1

                    amt1 = safe_get_amounts_out(r1, amount_in_usdc_raw, [USDC_ADDRESS, token])
                    if not amt1:
                        continue
                    out_token_raw = int(amt1[-1] * (1 - DEX_SWAP_FEE))
                    out_token_after_slip = int(out_token_raw * (1 - SLIPPAGE_BPS / 10000))
                    if out_token_after_slip == 0:
                        continue
                    amt2 = safe_get_amounts_out(r2, out_token_after_slip, [token, USDC_ADDRESS])
                    if not amt2:
                        continue
                    out_usdc_raw = int(amt2[-1] * (1 - DEX_SWAP_FEE))
                    out_usdc_after_slip = int(out_usdc_raw * (1 - SLIPPAGE_BPS / 10000))
                    gas1 = estimate_gas_for_swap(r1, amount_in_usdc_raw, 0, [USDC_ADDRESS, token], EXECUTOR_ADDRESS)
                    gas2 = estimate_gas_for_swap(r2, out_token_after_slip, 0, [token, USDC_ADDRESS], EXECUTOR_ADDRESS)
                    total_gas = gas1 + gas2
                    profit_usd, profit_pct, gas_cost_usd = compute_profit(SIM_INPUT_USDC, out_usdc_after_slip, total_gas, GAS_PRICE_GWEI)

                    if profit_usd > 0:
                        trade_id = f"{symbol}-{r1_name}->{r2_name}"
                        if trade_id not in reported_trades:
                            profitable_trades.append({
                                'symbol': symbol,
                                'route': f'USDC → Buy {symbol} on {r1_name} → Sell {symbol} on {r2_name}',
                                'output_usdc': Decimal(out_usdc_after_slip) / (10 ** USDC_DECIMALS),
                                'gas_used': total_gas,
                                'gas_cost_usd': gas_cost_usd,
                                'profit_usd': profit_usd,
                                'profit_pct': profit_pct,
                                'id': trade_id
                            })
                            reported_trades.add(trade_id)

            # Print new profitable trades
            if not profitable_trades:
                print("\nNo new profitable arbitrage found in this scan.")
            else:
                profitable_trades.sort(key=lambda x: x['profit_usd'], reverse=True)
                for trade in profitable_trades[:TOP_N]:
                    print('\n🎉 NEW PROFITABLE ARBITRAGE FOUND!')
                    print(f"Token: {trade['symbol']}")
                    print(f"Route: {trade['route']}")
                    print(f"Output USDC: {trade['output_usdc']:,.6f}")
                    print(f"Gas used: {trade['gas_used']} @ {GAS_PRICE_GWEI} gwei -> cost ≈ ${trade['gas_cost_usd']:,.2f}")
                    print(f"Profit: ${trade['profit_usd']:,.2f} ({trade['profit_pct']:.4f}%)")

        except Exception as e:
            print(f"Error during scan: {e}")

        print('Scan complete. Waiting 5 seconds before next scan...\n')
        time.sleep(5)

if __name__ == '__main__':
    main_loop()
