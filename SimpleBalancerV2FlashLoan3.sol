// SPDX-License-Identifier: MIT
pragma solidity ^0.8.10;

import "@balancer-labs/v2-interfaces/contracts/vault/IVault.sol";
import "@balancer-labs/v2-interfaces/contracts/vault/IFlashLoanRecipient.sol";

contract FlashLoanRecipient is IFlashLoanRecipient {
    IVault private constant vault = IVault(0xBA12222222228d8Ba445958a75a0704d566BF2C8);
    address private constant OWNER = 0xC3baC4665c47fb6DE24489982E80532943E47bE0;

    // Hardcoded USDC contract address (6 decimals)
    address private constant USDC = 0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913;
    uint256 private constant FLASH_LOAN_AMOUNT = 100000 * 1e6; // $100,000 USDC

    // Hardcoded version for $100k USDC flash loan
    function makeFlashLoan() external {
        IERC20[] memory tokens = new IERC20[](1);
        tokens[0] = IERC20(USDC); // Hardcoded USDC

        uint256[] memory amounts = new uint256[](1);
        amounts[0] = FLASH_LOAN_AMOUNT; // Hardcoded $100k USDC

        // Empty userData (can be extended if needed)
        bytes memory emptyUserData = "";

        vault.flashLoan(this, tokens, amounts, emptyUserData);
    }

    function receiveFlashLoan(
        IERC20[] memory tokens,
        uint256[] memory amounts,
        uint256[] memory feeAmounts,
        bytes memory userData
    ) external override {
        require(msg.sender == address(vault), "Caller must be Vault");

        // Repay the flash loan + fees
        for (uint256 i = 0; i < tokens.length; i++) {
            uint256 totalOwed = amounts[i] + feeAmounts[i];
            tokens[i].transfer(address(vault), totalOwed);
        }

        // Add your arbitrage/swap logic here
        // Example: Convert USDC to WETH and back with profit
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
