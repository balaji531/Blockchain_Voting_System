// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract Voting {
    address public owner;

    struct Candidate {
        uint id;
        string name;
        uint voteCount;
    }

    mapping(uint => Candidate) public candidates;
    uint public candidatesCount;

    mapping(address => bool) public registeredVoter;
    mapping(address => bool) public hasVoted;

    event VoterRegistered(address voter);
    event VoteCast(address voter, uint candidateId);

    modifier onlyOwner() {
        require(msg.sender == owner, "Only owner");
        _;
    }

    constructor() {
        owner = msg.sender;
    }

    function addCandidate(string memory _name) public onlyOwner {
        candidatesCount++;
        candidates[candidatesCount] = Candidate(candidatesCount, _name, 0);
    }

    function registerVoter(address _voter) public onlyOwner {
        require(!registeredVoter[_voter], "Already registered");
        registeredVoter[_voter] = true;
        emit VoterRegistered(_voter);
    }

    function castVote(uint _candidateId) public {
        require(registeredVoter[msg.sender], "Not registered");
        require(!hasVoted[msg.sender], "Already voted");
        require(_candidateId > 0 && _candidateId <= candidatesCount, "Invalid candidate");

        candidates[_candidateId].voteCount++;
        hasVoted[msg.sender] = true;

        emit VoteCast(msg.sender, _candidateId);
    }

    function getVoteCount(uint _candidateId) public view returns (uint) {
        require(_candidateId > 0 && _candidateId <= candidatesCount, "Invalid candidate");
        return candidates[_candidateId].voteCount;
    }

    function verifyVote(address _voter) public view returns (bool) {
        return hasVoted[_voter];
    }
}
