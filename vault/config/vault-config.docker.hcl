ui = true 
disable_mlock = true

storage "raft" {
    path = "/vault/data"
    # Note: node_id cannot be a list. If you share this config across containers,
    # remove node_id here and set VAULT_RAFT_NODE_ID in your docker-compose for each node.

    
    retry_join {
        leader_api_addr = "https://vault_1:8200"
        leader_ca_cert_file = "/vault/tls/public.crt"

    }
    
    retry_join {
        leader_api_addr = "https://vault_2:8200"
        leader_ca_cert_file = "/vault/tls/public.crt"

    }
    
    retry_join {
        leader_api_addr = "https://vault_3:8200"
        leader_ca_cert_file = "/vault/tls/public.crt"
    }
}

listener "tcp" {
    address = "0.0.0.0:8200"
    tls_disable = false
    tls_cert_file = "/vault/tls/public.crt"
    tls_key_file = "/vault/tls/private.crt"
}


