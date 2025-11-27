// SPDX-License-Identifier: MIT
pragma solidity 0.8.10;

import "@aave/core-v3/contracts/flashloan/base/FlashLoanSimpleReceiverBase.sol";
import "@aave/core-v3/contracts/interfaces/IPoolAddressesProvider.sol";
import "@aave/core-v3/contracts/dependencies/openzeppelin/contracts/IERC20.sol";

contract FlashloanAttacker is FlashLoanSimpleReceiverBase {
  IPoolAddressesProvider internal _provider;
  IPool internal _pool;

  constructor(IPoolAddressesProvider provider) FlashLoanSimpleReceiverBase(provider) {
    _pool = IPool(provider.getPool());
  }

    function requestFlashLoan(address _token, uint256 _amount) public {
        address receiverAddress = address(this);
        address asset = _token;
        uint256 amount = _amount;
        bytes memory params = "";
        uint16 referralCode = 0;

        POOL.flashLoanSimple(
            receiverAddress,
            asset,
            amount,
            params,
            referralCode
        );
    }

  function executeOperation(
    address asset,
    uint256 amount,
    uint256 premium,
    address, // initiator
    bytes memory // params
  ) public override returns (bool) {
    // Strategy to perform Arbitrage is inserted here.

    IERC20(asset).approve(address(POOL), amount + premium);

    return true;
  }
}
