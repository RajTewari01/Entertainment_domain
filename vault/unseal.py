"""
Cross-platform Vault auto-unseal script.

NOTE :
    >>> Reads unseal keys from vault/env.prod and unseals the Vault server.
Usage: 
    >>> $python vault/unseal.py
"""

from __future__ import annotations
from typing import List, Iterator, Pattern, Tuple,Final,Literal
import sys, subprocess, re
from pathlib import Path

def _ancestor(target:str|None=None)->Path:
    target : Final[str] = target or "Entertainment_domain"
    current : Final[Path] = Path(__file__).resolve()
    cwd = current

    while cwd.name != target:
        if cwd.parent == cwd:
            raise ValueError(f"Could not find ancestor '{target}'")
        cwd = cwd.parent
    return cwd

BaseDir : Final[Path] = _ancestor()
VaultDir : Final[Path] = BaseDir / "vault"
EnvFile : Final[Path] = VaultDir / ".env.prod"
Compose : Final[Path] = VaultDir / "docker-compose.yml"


class VaultConfig:
    KEY_PATTERN : Pattern[str] = re.compile(r"^VAULT_UNSEAL_KEY_[0-9]:=(?P<value>.*)$",re.MULTILINE)
    RUN_COMMAND_PREFIX : Tuple[str, ...] = (
            'docker', 'compose', '-f', str(Compose), 'exec', '-T'
        )
    
    def load_keys(self,path:Path|str|None=None)->List[str]:
        target : Path = Path(path).resolve() if path and Path(path).exists() else EnvFile
        
        if not target.exists():
            print(f"ERROR : {target} does not exist.",sep="\n",file=sys.stderr)
            sys.exit(1)
        
        with open(target,'r',encoding='utf-8') as file:
            text : Final[str] = file.read()
            keys_iter : Iterator[re.Match[str]] = self.KEY_PATTERN.finditer(text)
            return [match.group('value') for match in keys_iter]

    
    def unseal(self, key:str, server_name:str) -> 'VaultConfig':
        cmd : List[str] = list(self.RUN_COMMAND_PREFIX) + [
            server_name, 'vault', 'operator', 'unseal', '-tls-skip-verify', key
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            if "Vault is already unsealed" in result.stderr or "Vault is already unsealed" in result.stdout:
                print(f"[{server_name}] Already unsealed.")
            else:
                print(f"[{server_name}] Note: {result.stderr.strip() or result.stdout.strip()}")
        return self

def main()->None:
    '''
    NOTE : Fetches the unseal keys directly from the .env.prod file,
    injects them dynamically into the `docker compose exec` command,
    and runs them sequentially to unseal the Vault server.
    '''
    vlt : VaultConfig = VaultConfig()
    keys : List[str] | None = vlt.load_keys()

    if not keys:
        print(f"ERROR: No VAULT_UNSEAL_KEY_* entries found in {EnvFile.name}.", file=sys.stderr)
        sys.exit(1)
    
    print(f"Loaded {len(keys)} unseal keys.",file=sys.stdout)
    servers : Final[Tuple[str, ...]] = ('vault_server_1', 'vault_server_2', 'vault_server_3')
    
    for server in servers:
        print(f"\nUnsealing {server}...",file=sys.stdout)
        for index, key in enumerate(keys, start=1):
            print(f"Providing key {index}/{len(keys)} to {server}...",file=sys.stdout)
            vlt.unseal(key=key, server_name=server)
            
        if server != servers[-1]:
            print(f"Waiting 10 seconds for {server} to sync with the Raft cluster...", file=sys.stdout)

    
    print('\nVault cluster unseal process complete.',file=sys.stdout)

if __name__ == '__main__':
    main()



        
        
        

    
