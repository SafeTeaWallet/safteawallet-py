// SPDX-License-Identifier: MIT
pragma solidity ^0.8.29;

import "./Interfaces/ISafeTeaFactory.sol";

contract SafeTeaWallet {
    // Types
    enum OwnerProposalType {
        Add,
        Remove
    }

    // Transaction data - packed to save gas
    struct Transaction {
        address to;
        uint256 value;
        bytes data;
        uint32 createdAt;
        uint32 expiry;
        uint16 confirmations;
        uint16 rejections;
        uint8 status; // 0 = pending, 1 = executed, 2 = canceled/expired
    }

    // Owner change proposal - also packed nicely
    struct OwnerProposal {
        address proposedOwner;
        uint32 createdAt;
        uint32 expiry;
        uint16 confirmations;
        uint16 rejections;
        uint8 status; // 0 = pending, 1 = executed, 2 = canceled/expired
        OwnerProposalType proposalType;
    }

    // Storage
    ISafeTeaFactory public immutable safeTeaFactory;

    address[] public owners;
    mapping(address => bool) public isOwner;

    Transaction[] public transactions;
    OwnerProposal[] public ownerProposals;

    // Track who voted what (0 = no vote, 1 = confirm, 2 = reject)
    mapping(uint256 => mapping(address => uint8)) public txVotes;
    mapping(uint256 => mapping(address => uint8)) public proposalVotes;

    // Events
    event TransactionSubmitted(
        uint256 indexed txIndex,
        address indexed to,
        uint256 value
    );
    event TransactionConfirmed(uint256 indexed txIndex, address indexed owner);
    event TransactionRejected(uint256 indexed txIndex, address indexed owner);
    event TransactionExecuted(uint256 indexed txIndex);
    event TransactionCanceled(uint256 indexed txIndex);
    event TransactionExpired(uint256 indexed txIndex);

    event OwnerProposed(
        uint256 indexed proposalIndex,
        address indexed proposedOwner,
        OwnerProposalType indexed proposalType
    );
    event OwnerProposalConfirmed(
        uint256 indexed proposalIndex,
        address indexed owner
    );
    event OwnerProposalRejected(
        uint256 indexed proposalIndex,
        address indexed owner
    );
    event OwnerAdded(uint256 indexed proposalIndex, address indexed newOwner);
    event OwnerRemoved(
        uint256 indexed proposalIndex,
        address indexed removedOwner
    );
    event OwnerProposalCanceled(uint256 indexed proposalIndex);
    event OwnerProposalExpired(uint256 indexed proposalIndex);

    // Errors
    error NotOwner();
    error TxNotExist();
    error ProposalNotExist();
    error AlreadyVoted();
    error AlreadyFinalized();
    error Expired();
    error NotExpired();
    error ZeroAddress();
    error NotUnique();
    error InvalidExpiry();
    error AlreadyOwner();
    error NotAnOwner();
    error InsufficientConfirmations();
    error ExecutionFailed();
    error CannotRemoveLastOwner();

    // Modifiers
    modifier onlyOwner() {
        if (!isOwner[msg.sender]) revert NotOwner();
        _;
    }

    modifier validTx(uint256 txIndex) {
        if (txIndex >= transactions.length) revert TxNotExist();
        Transaction storage txn = transactions[txIndex];
        if (txn.status != 0) revert AlreadyFinalized();
        if (block.timestamp > txn.expiry) revert Expired();
        _;
    }

    modifier validProposal(uint256 proposalIndex) {
        if (proposalIndex >= ownerProposals.length) revert ProposalNotExist();
        OwnerProposal storage proposal = ownerProposals[proposalIndex];
        if (proposal.status != 0) revert AlreadyFinalized();
        if (block.timestamp > proposal.expiry) revert Expired();
        _;
    }

    constructor(address[] memory _owners, address _factory) {
        if (_owners.length < 2) revert NotUnique();
        if (_factory == address(0)) revert ZeroAddress();

        safeTeaFactory = ISafeTeaFactory(_factory);

        for (uint256 i; i < _owners.length; ++i) {
            address owner = _owners[i];
            if (owner == address(0)) revert ZeroAddress();
            if (isOwner[owner]) revert NotUnique();
            isOwner[owner] = true;
            owners.push(owner);
        }
    }

    receive() external payable {}

    // Returns how many votes needed for majority
    function getMajorityThreshold() public view returns (uint256) {
        return (owners.length >> 1) + 1;
    }

    // Submit a new transaction for owners to vote on
    function submitTransaction(
        address to,
        uint256 value,
        bytes calldata data,
        uint256 _expiry
    ) external onlyOwner returns (uint256 txIndex) {
        if (to == address(0)) revert ZeroAddress();
        if (_expiry <= block.timestamp || _expiry > block.timestamp + 30 days)
            revert InvalidExpiry();

        txIndex = transactions.length;
        transactions.push(
            Transaction({
                to: to,
                value: value,
                data: data,
                createdAt: uint32(block.timestamp),
                expiry: uint32(_expiry),
                confirmations: 0,
                rejections: 0,
                status: 0
            })
        );

        emit TransactionSubmitted(txIndex, to, value);
    }

    // Approve a transaction
    function confirmTransaction(
        uint256 txIndex
    ) external onlyOwner validTx(txIndex) {
        if (txVotes[txIndex][msg.sender] != 0) revert AlreadyVoted();

        txVotes[txIndex][msg.sender] = 1;
        uint16 confirms = ++transactions[txIndex].confirmations;

        emit TransactionConfirmed(txIndex, msg.sender);

        if (confirms >= getMajorityThreshold()) {
            _executeTransaction(txIndex);
        }
    }

    // Reject a transaction
    function rejectTransaction(
        uint256 txIndex
    ) external onlyOwner validTx(txIndex) {
        if (txVotes[txIndex][msg.sender] != 0) revert AlreadyVoted();

        txVotes[txIndex][msg.sender] = 2;
        uint16 rejects = ++transactions[txIndex].rejections;

        emit TransactionRejected(txIndex, msg.sender);

        if (rejects >= getMajorityThreshold()) {
            transactions[txIndex].status = 2;
            emit TransactionCanceled(txIndex);
        }
    }

    // Manually execute if needed (after majority confirmed)
    function executeTransaction(
        uint256 txIndex
    ) external onlyOwner validTx(txIndex) {
        if (transactions[txIndex].confirmations < getMajorityThreshold())
            revert InsufficientConfirmations();
        _executeTransaction(txIndex);
    }

    // Mark a stale transaction as expired
    function markTransactionExpired(uint256 txIndex) external {
        if (txIndex >= transactions.length) revert TxNotExist();
        Transaction storage txn = transactions[txIndex];
        if (txn.status != 0) revert AlreadyFinalized();
        if (block.timestamp <= txn.expiry) revert NotExpired();

        txn.status = 2;
        emit TransactionExpired(txIndex);
    }

    function _executeTransaction(uint256 txIndex) internal {
        Transaction storage txn = transactions[txIndex];
        txn.status = 1;

        (bool success, ) = txn.to.call{value: txn.value}(txn.data);
        if (!success) revert ExecutionFailed();

        emit TransactionExecuted(txIndex);
    }

    // Propose adding or removing an owner
    function proposeOwner(
        address proposedOwner,
        OwnerProposalType proposalType,
        uint256 _expiry
    ) external onlyOwner returns (uint256 proposalIndex) {
        if (proposedOwner == address(0)) revert ZeroAddress();
        if (_expiry <= block.timestamp || _expiry > block.timestamp + 30 days)
            revert InvalidExpiry();

        if (proposalType == OwnerProposalType.Add) {
            if (isOwner[proposedOwner]) revert AlreadyOwner();
        } else {
            if (!isOwner[proposedOwner]) revert NotAnOwner();
            if (owners.length <= 2) revert CannotRemoveLastOwner();
        }

        proposalIndex = ownerProposals.length;
        ownerProposals.push(
            OwnerProposal({
                proposedOwner: proposedOwner,
                createdAt: uint32(block.timestamp),
                expiry: uint32(_expiry),
                confirmations: 0,
                rejections: 0,
                status: 0,
                proposalType: proposalType
            })
        );

        emit OwnerProposed(proposalIndex, proposedOwner, proposalType);
    }

    // Approve an owner change proposal
    function confirmOwnerProposal(
        uint256 proposalIndex
    ) external onlyOwner validProposal(proposalIndex) {
        if (proposalVotes[proposalIndex][msg.sender] != 0)
            revert AlreadyVoted();

        proposalVotes[proposalIndex][msg.sender] = 1;
        uint16 confirms = ++ownerProposals[proposalIndex].confirmations;

        emit OwnerProposalConfirmed(proposalIndex, msg.sender);

        if (confirms >= getMajorityThreshold()) {
            _executeOwnerProposal(proposalIndex);
        }
    }

    // Reject an owner change proposal
    function rejectOwnerProposal(
        uint256 proposalIndex
    ) external onlyOwner validProposal(proposalIndex) {
        if (proposalVotes[proposalIndex][msg.sender] != 0)
            revert AlreadyVoted();

        proposalVotes[proposalIndex][msg.sender] = 2;
        uint16 rejects = ++ownerProposals[proposalIndex].rejections;

        emit OwnerProposalRejected(proposalIndex, msg.sender);

        if (rejects >= getMajorityThreshold()) {
            ownerProposals[proposalIndex].status = 2;
            emit OwnerProposalCanceled(proposalIndex);
        }
    }

    // Mark a stale owner proposal as expired
    function markOwnerProposalExpired(uint256 proposalIndex) external {
        if (proposalIndex >= ownerProposals.length) revert ProposalNotExist();
        OwnerProposal storage proposal = ownerProposals[proposalIndex];
        if (proposal.status != 0) revert AlreadyFinalized();
        if (block.timestamp <= proposal.expiry) revert NotExpired();

        proposal.status = 2;
        emit OwnerProposalExpired(proposalIndex);
    }

    function _executeOwnerProposal(uint256 proposalIndex) internal {
        OwnerProposal storage proposal = ownerProposals[proposalIndex];
        proposal.status = 1;

        if (proposal.proposalType == OwnerProposalType.Add) {
            if (isOwner[proposal.proposedOwner]) revert AlreadyOwner();
            owners.push(proposal.proposedOwner);
            isOwner[proposal.proposedOwner] = true;
            emit OwnerAdded(proposalIndex, proposal.proposedOwner);
        } else {
            if (!isOwner[proposal.proposedOwner]) revert NotAnOwner();
            if (owners.length <= 2) revert CannotRemoveLastOwner();

            uint256 len = owners.length;
            for (uint256 i; i < len; ++i) {
                if (owners[i] == proposal.proposedOwner) {
                    owners[i] = owners[len - 1];
                    owners.pop();
                    break;
                }
            }
            isOwner[proposal.proposedOwner] = false;
            emit OwnerRemoved(proposalIndex, proposal.proposedOwner);
        }

        safeTeaFactory.updateWalletOwners(owners);
    }

    // Full wallet snapshot for frontend use
    struct TransactionView {
        uint256 index;
        address to;
        uint256 value;
        bytes data;
        uint8 status;
        bool isExpired;
        uint16 confirmations;
        uint16 rejections;
        uint32 expiry;
        uint32 createdAt;
    }

    struct OwnerProposalView {
        uint256 index;
        address proposedOwner;
        OwnerProposalType proposalType;
        uint8 status;
        bool isExpired;
        uint16 confirmations;
        uint16 rejections;
        uint32 expiry;
        uint32 createdAt;
    }

    struct WalletInfo {
        address[] owners;
        uint256 ownerCount;
        uint256 majorityThreshold;
        uint256 balance;
        uint256 transactionCount;
        TransactionView[] allTransactions;
        uint256 ownerProposalCount;
        OwnerProposalView[] allOwnerProposals;
    }

    function getInfo() external view returns (WalletInfo memory info) {
        uint256 ts = block.timestamp;

        info.owners = owners;
        info.ownerCount = owners.length;
        info.majorityThreshold = getMajorityThreshold();
        info.balance = address(this).balance;

        // Transactions
        uint256 txLen = transactions.length;
        info.transactionCount = txLen;
        info.allTransactions = new TransactionView[](txLen);

        for (uint256 i; i < txLen; ++i) {
            Transaction storage txn = transactions[i];
            info.allTransactions[i] = TransactionView({
                index: i,
                to: txn.to,
                value: txn.value,
                data: txn.data,
                status: txn.status,
                isExpired: txn.status == 0 && ts > txn.expiry,
                confirmations: txn.confirmations,
                rejections: txn.rejections,
                expiry: txn.expiry,
                createdAt: txn.createdAt
            });
        }

        // Owner proposals
        uint256 pLen = ownerProposals.length;
        info.ownerProposalCount = pLen;
        info.allOwnerProposals = new OwnerProposalView[](pLen);

        for (uint256 i; i < pLen; ++i) {
            OwnerProposal storage p = ownerProposals[i];
            info.allOwnerProposals[i] = OwnerProposalView({
                index: i,
                proposedOwner: p.proposedOwner,
                proposalType: p.proposalType,
                status: p.status,
                isExpired: p.status == 0 && ts > p.expiry,
                confirmations: p.confirmations,
                rejections: p.rejections,
                expiry: p.expiry,
                createdAt: p.createdAt
            });
        }
    }

    // Simple getters
    function getOwners() external view returns (address[] memory) {
        return owners;
    }

    function getOwnerCount() external view returns (uint256) {
        return owners.length;
    }

    function getTransactionCount() external view returns (uint256) {
        return transactions.length;
    }

    function getOwnerProposalCount() external view returns (uint256) {
        return ownerProposals.length;
    }

    function getTransaction(
        uint256 index
    ) external view returns (TransactionView memory) {
        if (index >= transactions.length) revert TxNotExist();
        Transaction storage txn = transactions[index];
        return
            TransactionView({
                index: index,
                to: txn.to,
                value: txn.value,
                data: txn.data,
                status: txn.status,
                isExpired: txn.status == 0 && block.timestamp > txn.expiry,
                confirmations: txn.confirmations,
                rejections: txn.rejections,
                expiry: txn.expiry,
                createdAt: txn.createdAt
            });
    }

    function getOwnerProposal(
        uint256 index
    ) external view returns (OwnerProposalView memory) {
        if (index >= ownerProposals.length) revert ProposalNotExist();
        OwnerProposal storage p = ownerProposals[index];
        return
            OwnerProposalView({
                index: index,
                proposedOwner: p.proposedOwner,
                proposalType: p.proposalType,
                status: p.status,
                isExpired: p.status == 0 && block.timestamp > p.expiry,
                confirmations: p.confirmations,
                rejections: p.rejections,
                expiry: p.expiry,
                createdAt: p.createdAt
            });
    }

    function isTransactionExpired(
        uint256 txIndex
    ) external view returns (bool) {
        if (txIndex >= transactions.length) revert TxNotExist();
        Transaction storage txn = transactions[txIndex];
        return txn.status == 0 && block.timestamp > txn.expiry;
    }

    function isOwnerProposalExpired(
        uint256 proposalIndex
    ) external view returns (bool) {
        if (proposalIndex >= ownerProposals.length) revert ProposalNotExist();
        OwnerProposal storage p = ownerProposals[proposalIndex];
        return p.status == 0 && block.timestamp > p.expiry;
    }

    function hasConfirmedTransaction(
        uint256 txIndex,
        address owner
    ) external view returns (bool) {
        return txVotes[txIndex][owner] == 1;
    }

    function hasRejectedTransaction(
        uint256 txIndex,
        address owner
    ) external view returns (bool) {
        return txVotes[txIndex][owner] == 2;
    }

    function hasConfirmedOwnerProposal(
        uint256 proposalIndex,
        address owner
    ) external view returns (bool) {
        return proposalVotes[proposalIndex][owner] == 1;
    }

    function hasRejectedOwnerProposal(
        uint256 proposalIndex,
        address owner
    ) external view returns (bool) {
        return proposalVotes[proposalIndex][owner] == 2;
    }
}