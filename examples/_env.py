"""Environment configuration for resource examples."""
import os
from onlyfans_sdk import OFAuthLink

def require(name):
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"Set {name}")
    return value

def link():
    return OFAuthLink(require("OFAUTH_CLIENT_ID"), client_secret=require("OFAUTH_CLIENT_SECRET"), redirect_uri=require("OFAUTH_REDIRECT_URI"))

def access_token():
    return require("OFAUTH_ACCESS_TOKEN")

def linked_account_id():
    return require("OFAUTH_LINKED_ACCOUNT_ID")

def api_url():
    return os.environ.get("OFAUTH_API_URL", "https://api.ofauth.com")

API_URL = api_url()
