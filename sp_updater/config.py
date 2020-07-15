import os
from web3.auto import w3

SP_ADDRESS = w3.toChecksumAddress(os.environ['BN_SP_UPDATER_SP_ADDRESS'])
SP_ABI = '[{"inputs": [], "constant": true, "name": "name", "outputs": [{"type": "string", "name": ""}], "stateMutability": "view", "payable": false, "type": "function"}, {"inputs": [{"type": "address", "name": "spender"}, {"type": "uint256", "name": "value"}], "constant": false, "name": "approve", "outputs": [{"type": "bool", "name": ""}], "stateMutability": "nonpayable", "payable": false, "type": "function"}, {"inputs": [], "constant": true, "name": "totalSupply", "outputs": [{"type": "uint256", "name": ""}], "stateMutability": "view", "payable": false, "type": "function"}, {"inputs": [{"type": "address", "name": "from"}, {"type": "address", "name": "to"}, {"type": "uint256", "name": "value"}], "constant": false, "name": "transferFrom", "outputs": [{"type": "bool", "name": ""}], "stateMutability": "nonpayable", "payable": false, "type": "function"}, {"inputs": [], "constant": true, "name": "finance", "outputs": [{"type": "address", "name": ""}], "stateMutability": "view", "payable": false, "type": "function"}, {"inputs": [], "constant": true, "name": "decimals", "outputs": [{"type": "uint8", "name": ""}], "stateMutability": "view", "payable": false, "type": "function"}, {"inputs": [{"type": "address", "name": "spender"}, {"type": "uint256", "name": "addedValue"}], "constant": false, "name": "increaseAllowance", "outputs": [{"type": "bool", "name": ""}], "stateMutability": "nonpayable", "payable": false, "type": "function"}, {"inputs": [], "constant": false, "name": "unpause", "outputs": [], "stateMutability": "nonpayable", "payable": false, "type": "function"}, {"inputs": [{"type": "address", "name": "account"}], "constant": true, "name": "isPauser", "outputs": [{"type": "bool", "name": ""}], "stateMutability": "view", "payable": false, "type": "function"}, {"inputs": [{"type": "address", "name": "token"}], "constant": false, "name": "reclaimTokens", "outputs": [], "stateMutability": "nonpayable", "payable": false, "type": "function"}, {"inputs": [], "constant": true, "name": "paused", "outputs": [{"type": "bool", "name": ""}], "stateMutability": "view", "payable": false, "type": "function"}, {"inputs": [], "constant": false, "name": "renouncePauser", "outputs": [], "stateMutability": "nonpayable", "payable": false, "type": "function"}, {"inputs": [{"type": "address", "name": "account"}], "constant": true, "name": "balanceOf", "outputs": [{"type": "uint256", "name": ""}], "stateMutability": "view", "payable": false, "type": "function"}, {"inputs": [], "constant": false, "name": "renounceOwnership", "outputs": [], "stateMutability": "nonpayable", "payable": false, "type": "function"}, {"inputs": [{"type": "address", "name": "account"}], "constant": false, "name": "addPauser", "outputs": [], "stateMutability": "nonpayable", "payable": false, "type": "function"}, {"inputs": [], "constant": false, "name": "pause", "outputs": [], "stateMutability": "nonpayable", "payable": false, "type": "function"}, {"inputs": [], "constant": true, "name": "owner", "outputs": [{"type": "address", "name": ""}], "stateMutability": "view", "payable": false, "type": "function"}, {"inputs": [], "constant": true, "name": "isOwner", "outputs": [{"type": "bool", "name": ""}], "stateMutability": "view", "payable": false, "type": "function"}, {"inputs": [], "constant": true, "name": "symbol", "outputs": [{"type": "string", "name": ""}], "stateMutability": "view", "payable": false, "type": "function"}, {"inputs": [{"type": "address", "name": "account"}], "constant": false, "name": "addMinter", "outputs": [], "stateMutability": "nonpayable", "payable": false, "type": "function"}, {"inputs": [], "constant": false, "name": "renounceMinter", "outputs": [], "stateMutability": "nonpayable", "payable": false, "type": "function"}, {"inputs": [{"type": "address", "name": "_finance"}], "constant": false, "name": "setFinance", "outputs": [], "stateMutability": "nonpayable", "payable": false, "type": "function"}, {"inputs": [{"type": "address", "name": "spender"}, {"type": "uint256", "name": "subtractedValue"}], "constant": false, "name": "decreaseAllowance", "outputs": [{"type": "bool", "name": ""}], "stateMutability": "nonpayable", "payable": false, "type": "function"}, {"inputs": [{"type": "address", "name": "to"}, {"type": "uint256", "name": "value"}], "constant": false, "name": "transfer", "outputs": [{"type": "bool", "name": ""}], "stateMutability": "nonpayable", "payable": false, "type": "function"}, {"inputs": [{"type": "address", "name": "account"}], "constant": true, "name": "isMinter", "outputs": [{"type": "bool", "name": ""}], "stateMutability": "view", "payable": false, "type": "function"}, {"inputs": [{"type": "address", "name": "owner"}, {"type": "address", "name": "spender"}], "constant": true, "name": "allowance", "outputs": [{"type": "uint256", "name": ""}], "stateMutability": "view", "payable": false, "type": "function"}, {"inputs": [{"type": "address", "name": "newOwner"}], "constant": false, "name": "transferOwnership", "outputs": [], "stateMutability": "nonpayable", "payable": false, "type": "function"}, {"inputs": [{"indexed": false, "type": "address", "name": "account"}, {"indexed": false, "type": "bytes32", "name": "contextName"}, {"indexed": false, "type": "uint256", "name": "amount"}], "type": "event", "name": "SponsorshipsAssigned", "anonymous": false}, {"inputs": [{"indexed": false, "type": "address", "name": "tokenAddr"}, {"indexed": false, "type": "uint256", "name": "amount"}], "type": "event", "name": "ReclaimedTokens", "anonymous": false}, {"inputs": [{"indexed": false, "type": "address", "name": "financeAddr"}], "type": "event", "name": "FinanceSet", "anonymous": false}, {"inputs": [{"indexed": true, "type": "address", "name": "previousOwner"}, {"indexed": true, "type": "address", "name": "newOwner"}], "type": "event", "name": "OwnershipTransferred", "anonymous": false}, {"inputs": [{"indexed": true, "type": "address", "name": "account"}], "type": "event", "name": "MinterAdded", "anonymous": false}, {"inputs": [{"indexed": true, "type": "address", "name": "account"}], "type": "event", "name": "MinterRemoved", "anonymous": false}, {"inputs": [{"indexed": false, "type": "address", "name": "account"}], "type": "event", "name": "Paused", "anonymous": false}, {"inputs": [{"indexed": false, "type": "address", "name": "account"}], "type": "event", "name": "Unpaused", "anonymous": false}, {"inputs": [{"indexed": true, "type": "address", "name": "account"}], "type": "event", "name": "PauserAdded", "anonymous": false}, {"inputs": [{"indexed": true, "type": "address", "name": "account"}], "type": "event", "name": "PauserRemoved", "anonymous": false}, {"inputs": [{"indexed": true, "type": "address", "name": "from"}, {"indexed": true, "type": "address", "name": "to"}, {"indexed": false, "type": "uint256", "name": "value"}], "type": "event", "name": "Transfer", "anonymous": false}, {"inputs": [{"indexed": true, "type": "address", "name": "owner"}, {"indexed": true, "type": "address", "name": "spender"}, {"indexed": false, "type": "uint256", "name": "value"}], "type": "event", "name": "Approval", "anonymous": false}, {"inputs": [{"type": "address", "name": "account"}, {"type": "uint256", "name": "amount"}], "constant": false, "name": "mint", "outputs": [{"type": "bool", "name": ""}], "stateMutability": "nonpayable", "payable": false, "type": "function"}, {"inputs": [{"type": "bytes32", "name": "contextName"}, {"type": "uint256", "name": "amount"}], "constant": false, "name": "assignContext", "outputs": [], "stateMutability": "nonpayable", "payable": false, "type": "function"}, {"inputs": [{"type": "bytes32", "name": "contextName"}], "constant": true, "name": "totalContextBalance", "outputs": [{"type": "uint256", "name": ""}], "stateMutability": "view", "payable": false, "type": "function"}, {"inputs": [{"type": "address", "name": "account"}, {"type": "bytes32", "name": "contextName"}], "constant": true, "name": "contextBalance", "outputs": [{"type": "uint256", "name": ""}], "stateMutability": "view", "payable": false, "type": "function"}]'

SPONSOR_EVENT_CONTRACT_ABI = '[{"anonymous": false,"inputs": [{"indexed": false,"internalType": "address","name": "addr","type": "address"}],"name": "Sponsor","type": "event"}]'

INFURA_URL = os.environ['BN_SP_UPDATER_INFURA_URL']

CHUNK = 10000
RECHECK_CHUNK = 300
