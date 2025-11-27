// SPDX-License-Identifier: MIT
pragma solidity ^0.8.10;

import "@balancer-labs/v2-interfaces/contracts/vault/IVault.sol";
import "@balancer-labs/v2-interfaces/contracts/vault/IFlashLoanRecipient.sol";

contract FlashLoanRecipient is IFlashLoanRecipient {
    IVault private constant vault = IVault(0xbA1333333333a1BA1108E8412f11850A5C319bA9);

    function makeFlashLoan(
        IERC20[] memory tokens,
        uint256[] memory amounts,
        bytes memory userData
    ) external {
        vault.flashLoan(this, tokens, amounts, userData);
    }

    function receiveFlashLoan(
        IERC20[] memory tokens,
        uint256[] memory amounts,
        uint256[] memory feeAmounts,
        bytes memory userData
    ) external override {
        require(msg.sender == address(vault), "Caller must be Vault");
        // Example: perform your logic here (arbitrage, swap, etc.)
        // Repay the flashloan + fees
        for (uint256 i = 0; i < tokens.length; i++) {
            uint256 totalOwed = amounts[i] + feeAmounts[i];
            tokens[i].transfer(address(vault), totalOwed);
        }
    }
}
