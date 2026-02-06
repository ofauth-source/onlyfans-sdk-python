import os
from dotenv import load_dotenv
from onlyfans_sdk import OFAuthClient, account

load_dotenv()

def main():
    api_key = os.getenv('OFAUTH_API_KEY')
    if not api_key:
        raise ValueError('OFAUTH_API_KEY environment variable is required')

    client = OFAuthClient(api_key=api_key)

    print('🔑 OFAuth SDK - Basic Example\n')

    print('1. Getting account information...')
    whoami = account.whoami(client)
    print(f'   ✓ Account ID: {whoami["id"]}')
    print(f'   ✓ Organization: {whoami.get("name", "N/A")}')
    print(f'   ✓ Permissions: {", ".join(whoami["permissions"])}')
    print()

    print('2. Listing connections...')
    connections = account.list_connections(client)
    print(f'   ✓ Found {len(connections["list"])} connection(s)')
    
    for conn in connections['list']:
        print(f'   - {conn["id"]}')
        print(f'     Status: {conn["status"]}')
        print(f'     User: {conn["userData"]["username"]} (ID: {conn["userData"]["id"]})')
        print(f'     Imported: {"Yes" if conn["imported"] else "No"}')
    print()

    if connections['list']:
        first_connection = connections['list'][0]
        print(f'3. Getting settings for connection {first_connection["id"]}...')
        
        settings = account.get_connection_settings(
            client,
            first_connection['id']
        )
        
        vault_cache = settings.get('vaultCache', {})
        print(f'   ✓ Vault cache enabled: {"Yes" if vault_cache.get("enabled") else "No"}')
        if vault_cache.get('settingsOverrides'):
            auto_cache = vault_cache['settingsOverrides'].get('autoCacheVault', False)
            print(f'   ✓ Auto-cache vault: {"Yes" if auto_cache else "No"}')

    print('\n✅ Example completed successfully!')

if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        print(f'❌ Error: {error}')
        exit(1)
