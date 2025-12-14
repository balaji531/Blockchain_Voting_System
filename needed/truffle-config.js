module.exports = {
  networks: {
    development: {
      host: "127.0.0.1",
      port: 7545,        // Ganache GUI default RPC port
      network_id: "*"    // Match any network id
    }
  },
  compilers: {
    solc: {
      version: "0.8.0"   // match your pragma ^0.8.0
    }
  }
};
