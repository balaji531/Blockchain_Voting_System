<h1>PREVIEW</h1>
<img width="900" height="700" alt="image" src="https://github.com/user-attachments/assets/43b55520-7dac-4406-b31d-7830783cbdde" />
<img width="900" height="700" alt="image" src="https://github.com/user-attachments/assets/b535d0e8-38b3-40c0-b37f-a2de290fc74c" />
<img width="900" height="700" alt="image" src="https://github.com/user-attachments/assets/8d951242-c293-4517-9c6b-60dd485d3a8f" />
<img width="900" height="700" alt="image" src="https://github.com/user-attachments/assets/3c5b7d5c-522c-4107-a246-a9f2e1ff5ce3" />
<img width="900" height="700" alt="image" src="https://github.com/user-attachments/assets/1ffc75cc-be90-48ec-8fd1-341c80462622" />

<h3>STEPS</h3>
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

