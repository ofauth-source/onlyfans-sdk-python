import os
from dotenv import load_dotenv
from onlyfans_sdk import OFAuthClient

load_dotenv()

def main():
    api_key = os.getenv('OFAUTH_API_KEY')
    connection_id = os.getenv('OFAUTH_CONNECTION_ID')

    if not api_key:
        raise ValueError('OFAUTH_API_KEY environment variable is required')
    if not connection_id:
        raise ValueError('OFAUTH_CONNECTION_ID environment variable is required for proxy examples')

    client = OFAuthClient(api_key=api_key)

    print('🔑 OFAuth SDK - Proxy Example\n')
    print(f'Using connection: {connection_id}\n')

    print('1. GET request - Fetching user profile...')
    profile = client.proxy(
        '/users/me',
        connection_id=connection_id,
    )
    
    print(f'   ✓ Username: @{profile["username"]}')
    print(f'   ✓ Name: {profile["name"]}')
    print(f'   ✓ Subscribers: {profile.get("subscribersCount", 0)}')
    print()

    print('2. GET request with query params - Listing subscribers...')
    subscribers = client.proxy(
        '/subscriptions/subscribers',
        connection_id=connection_id,
        query={'limit': 5, 'offset': 0},
    )
    
    print(f'   ✓ Found {len(subscribers.get("list", []))} subscribers')
    if subscribers.get('list'):
        print(f'   ✓ First subscriber: @{subscribers["list"][0]["username"]}')
    print()

    print('3. POST request example (structure only, not executed)...')
    print('''
   Example POST to create a post:
   
   client.proxy(
       '/posts',
       method='POST',
       connection_id=connection_id,
       body={
           'text': 'Hello from OFAuth SDK!',
           'mediaIds': [],
           'price': 0,
       },
   )
    ''')

    print('✅ Example completed successfully!')

if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        print(f'❌ Error: {error}')
        exit(1)
