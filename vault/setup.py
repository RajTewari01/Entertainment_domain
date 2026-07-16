from __future__ import annotations
from typing import Final,Pattern,Tuple
from pathlib import Path
import hvac,re,sys


def _ancestor(target:str|None=None)->Path:
    """
    Returns the ancestor directory named 'target'
    """
    target : Final[str]= target or "Entertainment_domain"
    cwd : Final[Path]= Path(__file__).resolve()
    current : Path = cwd

    while current.name != target:
        if current.parent == current:
            raise ValueError(f"Could not find ancestor '{target}'")
        current = current.parent
    return current

BaseDir : Final[Path]= _ancestor()
VaultDir : Final[Path]= BaseDir/"vault"
EnvFile : Final[Path] = VaultDir/".env.prod"
Compose : Final[Path] = VaultDir/"docker-compose.yml"
Tls_cert : Final[Path] = VaultDir/ "tls/public.crt"

Pattern_Matching : Pattern[str] = re.compile(r'^VAULT_ROOT_TOKEN:=(?P<value>.*)$',re.MULTILINE)

def match_token(path:Path|str|None=None)->str:
    path : Final[Path] = Path(path).resolve() if path and Path(path).exists() else EnvFile
    if not path.exists():
        raise FileNotFoundError(f"No related file found at {path}")
    
    match = Pattern_Matching.search(path.read_text())
    if not match:
        raise ValueError(f"No token found in {path}")
    
    return match.group(1)

class AppRoleSetup:
    def __init__(self):
        self.token = match_token()
        self.client = hvac.Client(
            url='https://127.0.0.1:8200',
            token=self.token,
            verify=str(Tls_cert)
        )


    def setup(self)->Tuple[str,str]:
        if not self.client.is_authenticated():
            print("Error : Root token not valid. Please login using 'make vault_unseal' first.",file=sys.stderr)
            sys.exit(1)
        
        try:
            self.client.sys.enable_secrets_engine(
                backend_type='kv',
                path='secret', 
                options={'version': '2'}
            )
        except hvac.exceptions.InvalidRequest:
            print("KV-V2 Secrets Engine already enabled")
        
        POLICY : str = """
        path "secret/data/entertainment/*" {
            capabilities = ["create", "read", "update", "delete", "list"]
        }
        """

        self.client.sys.create_or_update_policy(
            name="Entertainment-approle-policy",
            policy=POLICY
        )         

        try:
            self.client.sys.enable_auth_method(method_type='approle')
            print("✅ Enabled AppRole Auth Method")
        except hvac.exceptions.InvalidRequest:
            print("⚡ AppRole Auth Method already enabled")   
        
        self.client.auth.approle.create_or_update_approle(
            role_name="Entertainment-approle",
            token_policies=["Entertainment-approle-policy"],
            token_ttl="1h",
            token_max_ttl="4h"
        )

        role_id_response : dict = self.client.auth.approle.read_role_id(role_name="Entertainment-approle")
        role_id : str = role_id_response['data']['role_id']

        secret_id_response : dict = self.client.auth.approle.generate_secret_id(role_name="Entertainment-approle")
        secret_id : str = secret_id_response['data']['secret_id']

        return(
            role_id,secret_id
        )

    
    def output_env(self)->'AppRoleSetup':
        role_id,secret_id = self.setup()
        with open(
            EnvFile,"a",encoding='utf-8'
        ) as file:
            file.write("\n"+ "# ===== APPROLE =====\n"  )
            file.write(f"VAULT_ROLE_ID={role_id}\n")
            print(f"Role ID : {role_id}",file=sys.stderr)
            file.write(f"VAULT_SECRET_ID={secret_id}\n")
            print(f"Secret ID : {secret_id}",file=sys.stderr)
        return self
    

if __name__ == '__main__':
    AppRoleSetup().output_env()
    print("AppRole setup complete.",file=sys.stdout)