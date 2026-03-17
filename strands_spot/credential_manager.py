import json
import os
import stat
from datetime import datetime
from pathlib import Path
from getpass import getpass


class SpotCredentialManager:
    def __init__(self):
        self.spot_dir = Path.home() / ".spot"
        self.spot_dir.mkdir(mode=0o700, exist_ok=True)
    
    def create_profile(self, name=None):
        if name is None:
            name = self._generate_auto_name()
        
        profile_path = self.spot_dir / f"{name}.json"
        if profile_path.exists():
            raise FileExistsError(f"Profile '{name}' already exists")
        
        credentials = self._prompt_credentials()
        self._save_profile(name, credentials)
        return name
    
    def replace_profile(self, name):
        credentials = self._prompt_credentials()
        self._save_profile(name, credentials)
        return name
    
    def load_profile(self, name):
        profile_path = self.spot_dir / f"{name}.json"
        if not profile_path.exists():
            raise FileNotFoundError(f"Profile '{name}' not found")
        
        with open(profile_path, 'r') as f:
            data = json.load(f)
        
        data['last_used'] = datetime.now().isoformat()
        with open(profile_path, 'w') as f:
            json.dump(data, f, indent=2)
        os.chmod(profile_path, 0o600)
        
        return data
    
    def _generate_auto_name(self):
        i = 0
        while (self.spot_dir / f"spotCredentials{i}.json").exists():
            i += 1
        return f"spotCredentials{i}"
    
    def _prompt_credentials(self):
        hostname = input("Hostname: ")
        username = input("Username: ")
        password = getpass("Password: ")
        
        return {
            "hostname": hostname,
            "username": username,
            "password": password,
            "created": datetime.now().isoformat(),
            "last_used": None
        }
    
    def _save_profile(self, name, credentials):
        profile_path = self.spot_dir / f"{name}.json"
        with open(profile_path, 'w') as f:
            json.dump(credentials, f, indent=2)
        os.chmod(profile_path, 0o600)