vault {
  address = "https://health_vault:8200"
  ca_cert = "/vault/tls/public.pem"
}

auto_auth {
  method "approle" {
    config = {
      role_id_file_path   = "/vault/approle/role-id"
      secret_id_file_path = "/vault/approle/secret-id"
    }
  }

  sink "file" {
    config = {
      path = "/vault/secrets/vault-token"
    }
  }
}

template {
  contents = <<-EOF
  {{with secret "secret/data/entertainment/monitoring"}}
  {{ .Data.data.GRAFANA_PASSWORD }}
  {{end}}
  EOF
  destination = "/vault/secrets/grafana-password"  
}

