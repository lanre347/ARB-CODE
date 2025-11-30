// SPDX-License-Identifier: MIT
pragma solidity ^0.8.10;

import "@balancer-labs/v2-interfaces/contracts/vault/IVault.sol";
import "@balancer-labs/v2-interfaces/contracts/vault/IFlashLoanRecipient.sol";

contract FlashLoanRecipient is IFlashLoanRecipient {
    IVault private constant vault = IVault(0xBA12222222228d8Ba445958a75a0704d566BF2C8);
    address private constant OWNER = 0xC3baC4665c47fb6DE24489982E80532943E47bE0;

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

    function withdrawETH() external {
        require(msg.sender == OWNER, "Only owner");
        uint256 balance = address(this).balance;
        require(balance > 0, "No ETH to withdraw");
        payable(OWNER).transfer(balance);
    }

    receive() external payable {}
    fallback() external payable {}
}
