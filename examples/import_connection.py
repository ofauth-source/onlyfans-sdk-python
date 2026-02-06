import os
from dotenv import load_dotenv
from onlyfans_sdk import OFAuthClient, account

load_dotenv()

def main():
    api_key = os.getenv('OFAUTH_API_KEY')
    if not api_key:
        raise ValueError('OFAUTH_API_KEY environment variable is required')

    client = OFAuthClient(api_key=api_key)

    print('🔑 OFAuth SDK - Import Connection Example\n')

    example_cookie = 'sess=your_session; auth_id=12345; auth_uid_12345=xxx; fp=yyy'
    example_user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'

    print('⚠️  This example requires valid OnlyFans session data.')
    print('    Update the cookie and user_agent variables with real values.\n')

    """
    imported = account.create_connections_connections_import(
        client,
        body={
            'cookie': example_cookie,
            'userAgent': example_user_agent,
            'permissions': ['profile:read', 'posts:read', 'messages:read'],
        }
    )
    
    print(f'   ✓ Connection imported: {imported["id"]}')
    print(f'   ✓ Status: {imported["status"]}')
    print(f'   ✓ User: {imported["userData"]["username"]} (ID: {imported["userData"]["id"]})')
    print()

    print('2. Updating imported connection session...')
    updated = account.update_connections_connections_import(
        client,
        imported['id'],
        body={
            'cookie': example_cookie,
            'userAgent': example_user_agent,
        }
    )
    
    print(f'   ✓ Session updated for: {updated["id"]}')
    print(f'   ✓ New status: {updated["status"]}')
    print()
    """

    print('3. Listing connections (showing imported flag)...')
    connections = account.list_connections(client)
    
    imported = [c for c in connections['list'] if c['imported']]
    managed = [c for c in connections['list'] if not c['imported']]
    
    print(f'   ✓ Total: {len(connections["list"])} connections')
    print(f'   ✓ Imported: {len(imported)}')
    print(f'   ✓ Managed: {len(managed)}')
    print()

    if imported:
        print('   Imported connections:')
        for conn in imported:
            print(f'   - {conn["id"]} ({conn["userData"]["username"]}) - {conn["status"]}')

    print('\n✅ Example completed!')

if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        print(f'❌ Error: {error}')
        exit(1)
