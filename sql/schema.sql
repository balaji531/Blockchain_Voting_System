CREATE DATABASE IF NOT EXISTS votingdb;
USE votingdb;

-- users, elections, candidates, votes
CREATE TABLE users (
  id INT AUTO_INCREMENT PRIMARY KEY,
  username VARCHAR(100) NOT NULL,
  email VARCHAR(150) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  voter_id VARCHAR(100) NOT NULL UNIQUE,
  role ENUM('voter','admin') DEFAULT 'voter',
  blockchain_address VARCHAR(255),
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE elections (
  id INT AUTO_INCREMENT PRIMARY KEY,
  is_active TINYINT(1) DEFAULT 0,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE candidates (
  id INT AUTO_INCREMENT PRIMARY KEY,
  candidate_number INT UNIQUE,
  name VARCHAR(100),
  party VARCHAR(100),
  age INT,
  qualification VARCHAR(200),
  description TEXT,
  is_verified TINYINT(1) DEFAULT 0
);

CREATE TABLE votes (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  candidate_id INT NOT NULL,
  election_id INT NOT NULL,
  tx_hash VARCHAR(255),
  UNIQUE KEY unique_vote (user_id, election_id),
  FOREIGN KEY (user_id) REFERENCES users(id),
  FOREIGN KEY (candidate_id) REFERENCES candidates(id),
  FOREIGN KEY (election_id) REFERENCES elections(id)
);
