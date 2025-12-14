import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key')
    # Example MySQL URI: mysql://user:pass@localhost/votingdb
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'mysql://root:@localhost/votingdb')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Web3 / Blockchain config (local Ganache)
    WEB3_PROVIDER = os.environ.get('WEB3_PROVIDER', 'http://127.0.0.1:7545')
    CONTRACT_ABI_PATH = os.environ.get('CONTRACT_ABI_PATH', 'build/contracts/Voting.json')
    CONTRACT_ADDRESS = os.environ.get('CONTRACT_ADDRESS', '...')  # Fill after deploying
    PRIVATE_KEY = os.environ.get('PRIVATE_KEY', '.......')  # Fill with your Ganache account private key