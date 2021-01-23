# TODO: Add tests that show proper operation of this strategy through "emergencyExit"
#       Make sure to demonstrate the "worst case losses" as well as the time it takes

import pytest

from brownie import Wei, accounts, Contract, config
from brownie import StrategyDAI3Pool


@pytest.mark.require_network("mainnet-fork")
def test_operation(pm, chain):
    dai_liquidity = accounts.at(
        "0xbebc44782c7db0a1a60cb6fe97d0b483032ff1c7", force=True
    )  # using curve pool (lots of dai)

    rewards = accounts[2]
    gov = accounts[3]
    guardian = accounts[4]
    bob = accounts[5]
    alice = accounts[6]
    strategist = accounts[7]
    tinytim = accounts[8]

    dai = Contract("0x6b175474e89094c44da98b954eedeac495271d0f", owner=gov)  # DAI token

    dai.approve(dai_liquidity, Wei("1000000 ether"), {"from": dai_liquidity})
    dai.transferFrom(dai_liquidity, gov, Wei("10000 ether"), {"from": dai_liquidity})

    # config yvDAI vault.
    Vault = pm(config["dependencies"][0]).Vault
    yUSDT3 = gov.deploy(Vault, dai, gov, rewards, "", "")

    threePool = Contract(
        "0xbEbc44782C7dB0a1A60Cb6fe97d0b483032FF1C7", owner=gov
    )  # crv3 pool address (threePool)
    crv3 = Contract(
        "0x6c3F90f043a72FA612cbac8115EE7e52BDe6E490", owner=gov
    )  # crv3 token address (threePool)
    yCRV3 = Contract(
        "0x9cA85572E6A3EbF24dEDd195623F188735A5179f", owner=gov
    )  # crv3 vault (threePool)
    # uni = Contract.from_explorer(
    #  "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D", owner=gov
    # )  # UNI router v2

    strategy = guardian.deploy(StrategyDAI3Pool, yUSDT3, dai, threePool, yCRV3, crv3)
    strategy.setStrategist(strategist)

    yUSDT3.addStrategy(
        strategy, Wei("1000000000 ether"), 2 ** 256 - 1, 50, {"from": gov}
    )

    dai.approve(gov, Wei("1000000 ether"), {"from": gov})
    dai.transferFrom(gov, bob, Wei("1000 ether"), {"from": gov})
    dai.transferFrom(gov, alice, Wei("4000 ether"), {"from": gov})
    dai.transferFrom(gov, tinytim, Wei("10 ether"), {"from":gov})
    dai.approve(yUSDT3, Wei("1000000 ether"), {"from": bob})
    dai.approve(yUSDT3, Wei("1000000 ether"), {"from": alice})
    dai.approve(yUSDT3, Wei("1000000 ether"), {"from": tinytim})
    crv3.approve(gov, Wei("1000000 ether"), {"from": gov})
    yUSDT3.approve(gov, Wei("1000000 ether"), {"from": gov})
    crv3.approve(yCRV3, Wei("1000000 ether"), {"from": gov})
    dai.approve(threePool, Wei("1000000 ether"), {"from": gov})

    # users deposit to vault
    yUSDT3.deposit(Wei("1000 ether"), {"from": bob})
    yUSDT3.deposit(Wei("4000 ether"), {"from": alice})
    yUSDT3.deposit(Wei("10 ether"), {"from": tinytim})

    chain.mine(1)

    strategy.harvest({"from": gov})

    assert 1 == 2

    strategy.setEmergencyExit({"from": gov})
    strategy.harvest({"from": gov})

    assert dai.balanceOf(yUSDT3) > 0
    assert yCRV3.balanceOf(strategy) == 0

    yUSDT3.withdraw({"from": alice})

    assert dai.balanceOf(alice) > 0
    assert dai.balanceOf(strategy) == 0
    assert dai.balanceOf(yUSDT3) > 0
    assert dai.balanceOf(bob) == 0

    yUSDT3.withdraw({"from": bob})

    assert dai.balanceOf(bob) > 0
    assert dai.balanceOf(strategy) == 0

    assert 1 == 2

    ##crv3.transferFrom(gov, bob, Wei("100000 ether"), {"from": gov})
    ##crv3.transferFrom(gov, alice, Wei("788000 ether"), {"from": gov})

    # yUSDT.deposit(Wei("100000 ether"), {"from": bob})
    # yUSDT.deposit(Wei("788000 ether"), {"from": alice})

    # strategy.harvest()

    # assert dai.balanceOf(strategy) == 0
    # assert yUSDT3.balanceOf(strategy) > 0
    # assert ycrv3.balanceOf(strategy) > 0

    # ycrv3.transferFrom(gov, strategy, Wei("1000 ether"), {"from":gov})
    # strategy.harvest({"from": gov})

    # We should have made profit
    # assert yUSDT3.pricePerShare() > 1

    # pass