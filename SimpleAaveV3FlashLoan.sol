// SPDX-License-Identifier: MIT
pragma solidity ^0.8.10;

import "https://github.com/aave/aave-v3-core/blob/master/contracts/flashloan/base/FlashLoanSimpleReceiverBase.sol";
import "https://github.com/aave/aave-v3-core/blob/master/contracts/interfaces/IPoolAddressesProvider.sol";
import "https://github.com/aave/aave-v3-core/blob/master/contracts/dependencies/openzeppelin/contracts/IERC20.sol";

contract SimpleAaveV3FlashLoan is FlashLoanSimpleReceiverBase {
    constructor(address _addressProvider)
        FlashLoanSimpleReceiverBase(IPoolAddressesProvider(_addressProvider))
    {}

    function requestFlashLoan(address token, uint256 amount) external {
        address receiver = address(this);
        bytes memory params = "";
        uint16 referralCode = 0;

        POOL.flashLoanSimple(receiver, token, amount, params, referralCode);
    }

    /// This function is called by Aave after loan is sent to this contract
    function executeOperation(
        address asset,
        uint256 amount,
        uint256 premium,
        address initiator,
        bytes calldata params
    ) external override returns (bool) {
        // --- you can add your logic here: arbitrage, swaps, etc. ---
        // For now just repay:
        uint256 totalOwed = amount + premium;
        IERC20(asset).approve(address(POOL), totalOwed);
        return true;
    }

    // allow contract to receive ETH (if needed)
    receive() external payable {}
}
