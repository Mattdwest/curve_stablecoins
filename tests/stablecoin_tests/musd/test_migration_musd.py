# TODO: Add tests here that show the normal operation of this strategy
#       Suggestions to include:
#           - strategy loading and unloading (via Vault addStrategy/revokeStrategy)
#           - change in loading (from low to high and high to low)
#           - strategy operation at different loading levels (anticipated and "extreme")

import pytest

from brownie import Wei, accounts, Contract, config
from brownie import StrategyDAImUSDv2


@pytest.mark.require_network("mainnet-fork")
def test_operation(pm, chain):
    dai_liquidity = accounts.at(
        "0xbebc44782c7db0a1a60cb6fe97d0b483032ff1c7", force=True
    )  # using curve pool (lots of dai)

    crv3_liquidity =  accounts.at(
        "0x6c3F90f043a72FA612cbac8115EE7e52BDe6E490", force=True
    )  # yearn treasury (lots of crv3)

    altCRV_liquidity = accounts.at(
        "0xe6e6e25efda5f69687aa9914f8d750c523a1d261", force=True
    )  # giant amount

    rewards = accounts[2]
    gov = accounts[3]
    guardian = accounts[4]
    bob = accounts[5]
    alice = accounts[6]
    strategist = accounts[7]
    tinytim = accounts[8]

    dai = Contract("0x6b175474e89094c44da98b954eedeac495271d0f", owner=gov)  # DAI token

    dai.approve(dai_liquidity, Wei("1000000 ether"), {"from": dai_liquidity})
    dai.transferFrom(dai_liquidity, gov, Wei("300000 ether"), {"from": dai_liquidity})

    crv3 = Contract(
        "0x6c3F90f043a72FA612cbac8115EE7e52BDe6E490", owner=gov
    )  # crv3 token address (threePool)

    altCRV = Contract(
        "0x1AEf73d49Dedc4b1778d0706583995958Dc862e6", owner=gov
    )  # altCRV token (mUSDCrv)

    crv3.approve(crv3_liquidity, Wei("1000000 ether"), {"from": crv3_liquidity})
    crv3.transferFrom(crv3_liquidity, gov, Wei("100 ether"), {"from": crv3_liquidity})

    altCRV.approve(altCRV_liquidity, Wei("1000000 ether"), {"from": altCRV_liquidity})
    altCRV.transferFrom(altCRV_liquidity, gov, Wei("1000 ether"), {"from": altCRV_liquidity})

    # config dai vault.
    Vault = pm(config["dependencies"][0]).Vault
    yDAI = Vault.deploy({"from": gov})
    yDAI.initialize(dai, gov, rewards, "", "",{"from": gov})
    yDAI.setDepositLimit(Wei("1000000 ether"))

    threePool = Contract(
        "0xbEbc44782C7dB0a1A60Cb6fe97d0b483032FF1C7", owner=gov
    )  # crv3 pool address (threePool)
    altCrvPool = Contract(
        "0x8474DdbE98F5aA3179B3B3F5942D724aFcdec9f6", owner=gov
    )  # atlCrvPool pool address (musdCrv)
    targetVault = Contract(
        "0x0FCDAeDFb8A7DfDa2e9838564c5A1665d856AFDF", owner=gov
    )  # target vault (musdCrv)
    targetVaultStrat = Contract(
        "0xBA0c07BBE9C22a1ee33FE988Ea3763f21D0909a0", owner=gov
    )  # targetVault strat (threePool)
    targetVaultStratOwner = Contract(
        "0xFEB4acf3df3cDEA7399794D0869ef76A6EfAff52", owner=gov
    )  # targetVault stratOwner (threePool)


    strategy = guardian.deploy(StrategyDAImUSDv2, yDAI, dai, threePool, targetVault, crv3, altCRV, altCrvPool)
    strategy.setStrategist(strategist)

    yDAI.addStrategy(
        strategy, 10_000, 0, 0, {"from": gov}
    )

    dai.approve(gov, Wei("1000000 ether"), {"from": gov})
    dai.transferFrom(gov, bob, Wei("1000 ether"), {"from": gov})
    dai.transferFrom(gov, alice, Wei("4000 ether"), {"from": gov})
    dai.transferFrom(gov, tinytim, Wei("10 ether"), {"from":gov})
    dai.approve(yDAI, Wei("1000000 ether"), {"from": bob})
    dai.approve(yDAI, Wei("1000000 ether"), {"from": alice})
    dai.approve(yDAI, Wei("1000000 ether"), {"from": tinytim})
    crv3.approve(gov, Wei("1000000 ether"), {"from": gov})
    yDAI.approve(gov, Wei("1000000 ether"), {"from": gov})
    targetVault.approve(gov, Wei("1000000 ether"), {"from": gov})
    altCRV.approve(gov, Wei("1000000 ether"), {"from": gov})
    dai.approve(threePool, Wei("1000000 ether"), {"from": gov})
    crv3.approve(altCrvPool, Wei("1000000 ether"), {"from": gov})

    targetVaultStrat.setStrategistReward(0, {"from": targetVaultStratOwner})
    targetVaultStrat.setTreasuryFee(0, {"from": targetVaultStratOwner})
    targetVaultStrat.setWithdrawalFee(0, {"from": targetVaultStratOwner})

    # users deposit to vault
    yDAI.deposit(Wei("1000 ether"), {"from": bob})
    yDAI.deposit(Wei("4000 ether"), {"from": alice})
    yDAI.deposit(Wei("10 ether"), {"from": tinytim})

    a = yDAI.pricePerShare()

    chain.mine(1)

    strategy.harvest({"from": gov})

    newstrategy = guardian.deploy(StrategyDAImUSDv2, yDAI, dai, threePool, targetVault, crv3, altCRV, altCrvPool)
    newstrategy.setStrategist(strategist)

    yDAI.migrateStrategy(strategy, newstrategy, {"from": gov})

    assert targetVault.balanceOf(strategy) == 0
    assert targetVault.balanceOf(newstrategy) > 0

    pass
