import json
import os
from web3 import Web3
from eth_utils import to_checksum_address

class BlockchainClient:
    def __init__(self, app=None):
        self.w3 = None
        self.contract = None
        self.contract_abi = None
        self.contract_address = None
        self.private_key = None
        if app:
            self.init_app(app)

    def init_app(self, app):
        self.w3 = Web3(Web3.HTTPProvider(app.config.get('WEB3_PROVIDER')))
        # Some local providers (Ganache) may not support ENS; avoid unexpected behavior
        try:
            self.w3.ens = None
        except Exception:
            pass

        self.private_key = app.config.get('PRIVATE_KEY')

        # Load ABI JSON robustly
        self.contract_abi = None
        abi_path = app.config.get('CONTRACT_ABI_PATH')
        if abi_path and os.path.exists(abi_path):
            try:
                with open(abi_path, 'r') as f:
                    js = json.load(f)
                    # Truffle artifact: has "abi" key. Some build tools produce the ABI directly.
                    if isinstance(js, dict) and 'abi' in js:
                        self.contract_abi = js['abi']
                    elif isinstance(js, list):
                        self.contract_abi = js
                    else:
                        # try to find nested abi
                        if 'output' in js and 'abi' in js['output']:
                            self.contract_abi = js['output']['abi']
                        elif 'contracts' in js:
                            # try to pull the first contract ABI
                            for k, v in js['contracts'].items():
                                if isinstance(v, dict) and 'abi' in v:
                                    self.contract_abi = v['abi']
                                    break
            except Exception:
                self.contract_abi = None

        self.contract_address = app.config.get('CONTRACT_ADDRESS') or None

        # instantiate contract only when we have both a valid address and ABI
        if self.contract_address and self.contract_abi:
            try:
                checksum_address = to_checksum_address(self.contract_address)
                self.contract = self.w3.eth.contract(address=checksum_address, abi=self.contract_abi)
                self.contract_address = checksum_address
            except Exception:
                # If something goes wrong, leave contract as None
                self.contract = None

    def set_contract(self, address, abi):
        if not self.w3:
            raise RuntimeError("Web3 provider not initialized")
        checksum_address = to_checksum_address(address)
        self.contract_address = checksum_address
        self.contract_abi = abi
        self.contract = self.w3.eth.contract(address=checksum_address, abi=abi)

    # --------------------------------------------------------------------------
    # TRANSACTION HELPER (Web3.py v6+ compatible)
    # --------------------------------------------------------------------------
    def _send_tx(self, func, private_key, from_address, gas=None):
        """
        Build, sign and send a transaction calling the given contract function (func).
        - func must be the contract function object with build_transaction() support.
        - private_key is the hex string of the sender's private key.
        - from_address is the sending address (checksum or hex).
        """
        account = self.w3.eth.account.from_key(private_key)
        if from_address:
            from_address = to_checksum_address(from_address)
        else:
            from_address = account.address

        nonce = self.w3.eth.get_transaction_count(from_address)

        chain_id = None
        try:
            chain_id = self.w3.eth.chain_id
        except Exception:
            # fallback: Ganache often supports chain_id 1337 or 5777; leave None if unknown
            chain_id = None

        # Build tx using build_transaction (Web3.py v6+)
        tx_params = {
            "from": from_address,
            "nonce": nonce,
        }
        # include chainId if available
        if chain_id:
            tx_params["chainId"] = chain_id

        # gas: either provided or estimate
        try:
            if gas:
                tx_params["gas"] = gas
            else:
                tx_params["gas"] = func.estimate_gas({"from": from_address})
        except Exception:
            # fallback
            tx_params["gas"] = 300000

        try:
            tx_params["gasPrice"] = self.w3.eth.gas_price
        except Exception:
            # Ganache may return 0; leave out if unavailable
            pass

        # build the tx dict
        built = func.build_transaction(tx_params)

        # sign transaction
        signed = self.w3.eth.account.sign_transaction(built, private_key)
        raw = signed.raw_transaction
        tx_hash = self.w3.eth.send_raw_transaction(raw)
        return tx_hash.hex()

    # --------------------------------------------------------------------------
    # REGISTER VOTER (admin only)
    # --------------------------------------------------------------------------
    def register_voter(self, admin_private_key, voter_address):
        if not self.contract:
            raise RuntimeError("Contract not set")

        voter_address = to_checksum_address(voter_address)
        admin_address = self.w3.eth.account.from_key(admin_private_key).address

        func = self.contract.functions.registerVoter(voter_address)
        return self._send_tx(func, admin_private_key, admin_address, gas=300000)

    # --------------------------------------------------------------------------
    # ADD CANDIDATE (admin only)
    # --------------------------------------------------------------------------
    def add_candidate(self, admin_private_key, name):
        if not self.contract:
            raise RuntimeError("Contract not set")

        admin_address = self.w3.eth.account.from_key(admin_private_key).address
        func = self.contract.functions.addCandidate(name)
        return self._send_tx(func, admin_private_key, admin_address, gas=400000)

    # --------------------------------------------------------------------------
    # CAST VOTE (voter)
    # --------------------------------------------------------------------------
    def cast_vote(self, voter_private_key, candidate_number, from_address):
        if not self.contract:
            raise RuntimeError("Contract not set")

        from_address = to_checksum_address(from_address)
        func = self.contract.functions.castVote(int(candidate_number))
        return self._send_tx(func, voter_private_key, from_address, gas=300000)

    # --------------------------------------------------------------------------
    # GET VOTE COUNT
    # --------------------------------------------------------------------------
    def get_vote_count(self, candidate_number):
        if not self.contract:
            return 0

        try:
            return self.contract.functions.getVoteCount(int(candidate_number)).call()
        except Exception:
            return 0

    # --------------------------------------------------------------------------
    # VERIFY VOTE
    # --------------------------------------------------------------------------
    def verify_vote(self, voter_address):
        if not self.contract:
            return False

        voter_address = to_checksum_address(voter_address)
        try:
            return self.contract.functions.verifyVote(voter_address).call()
        except Exception:
            return False
