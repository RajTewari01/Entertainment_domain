from __future__ import annotations
from typing import Final,Pattern
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
    path : Final[Path] = Path(path) or EnvFile
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


    def setup(self):
        if not self.client.is_authenticated():
            print("Error : Root token not valid. Please login using 'make vault_unseal' first.",file=sys.stderr)
            sys.exit(1)
        
        try:
            self.client.enable_secrets_engine(
                backend_type='kv',
                path='secret', 
                options={'version': '2'}
            )
        except hvac.excepions.InvalidRequest:
            print("KV-V2 Secrets Engine already enabled")
        
        POLICY : str = """
        path "secret/data/sora/*" {{
            capabilities = ["create", "read", "update", "delete", "list"]
        }}
        """

        
        self.client.hsm.create_policy(
            name="sora-approle-policy",
            policy=POLICY
        )            