What you get
- Solidity smart contract: contracts/Voting.sol
- Truffle migration + config to deploy on Ganache
- Flask backend with user registration, login, admin, voting endpoints
- MySQL schema to create required tables (sql/schema.sql)
- `backend/.env.example` shows required env variables

Quick Run Guide (local):

Install dependencies:
   1. python(3.9+)
   2. MYSQL (XAMPP Recpmmended)
   3. Ganache
   4. Node

Steps
1. Start Ganache (default RPC http://127.0.0.1:7545). Note one account's private key.

2. Deploy contract:
   CMD:
      npm install -g truffle
      truffle init
      truffle compile
      truffle migrate --network development
   
   Copy the deployed contract address from the migration output.

3. Prepare MySQL:
    Start MySQL (XAMPP)
    Create db name in Xampp as `Votingdb`

4. Backend setup:
   CMD:
      cd backend~
      python -m venv venv
      venv\Scripts\activate
      pip install -r requirements.txt
   
5. Go to .env file
      Replace CONTRACT_ADDRESS (from step 2) and PRIVATE_KEY (Ganache admin/private key)

6. Go to the Config.py 
      Replace CONTRACT_ADDRESS (from step 2) and PRIVATE_KEY (Ganache admin/private key) as same in the .env file

7. Create the `voting.sol` in the `backend/contract`. Copy and paste the code of `voting.sol` code from the needed folder

8. Create the `2_deploy_voting.js` in the `backend/migrations`. Copy and paste the code of  `2_deploy_voting.js` code from the needed folder

9. Copy the code in the `needed/truffle-config.js` and paste into the `backend/truffle-config.py` 

10. Open the Ganache click on the `Contracts` click `Link Truffle Projects`. Click `Add Projects` and add your truffle-config.js in the ganache. After click save and restart.

11. Run backend:
   CMD:
      python app.py
   
   Visit http://127.0.0.1:5000 


After register, update the role from vote to admin by code `Update users set role='admin' where id="Your_id" ` to access the admin panel.