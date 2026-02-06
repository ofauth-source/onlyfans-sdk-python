import os
from dotenv import load_dotenv
from onlyfans_sdk import OFAuthClient, OFAuthError, account

load_dotenv()

def main():
    api_key = os.getenv('OFAUTH_API_KEY')
    if not api_key:
        raise ValueError('OFAUTH_API_KEY environment variable is required')

    client = OFAuthClient(api_key=api_key)

    print('🔑 OFAuth SDK - Error Handling Example\n')

    print('1. Testing invalid API key error...')
    try:
        bad_client = OFAuthClient(api_key='invalid_key')
        account.whoami(bad_client)
    except OFAuthError as error:
        print(f'   ✓ Caught error: {error.message}')
        print(f'   ✓ Status: {error.status}')
        if error.code:
            print(f'   ✓ Error code: {error.code}')
    print()

    print('2. Testing not found error...')
    try:
        account.get_connection_settings(client, 'conn_nonexistent')
    except OFAuthError as error:
        print(f'   ✓ Caught error: {error.message}')
        print(f'   ✓ Status: {error.status}')
    except Exception as error:
        print(f'   ✓ Caught error: {error}')
    print()

    print('3. Testing successful request...')
    try:
        whoami = account.whoami(client)
        print(f'   ✓ Success! Account ID: {whoami["id"]}')
    except Exception as error:
        print(f'   ✗ Unexpected error: {error}')
    print()

    print('4. Error handling pattern example:')
    print('''
   try:
       result = account.whoami(client)
   except OFAuthError as error:
       if error.status == 401:
           print('Invalid API key')
       elif error.status == 404:
           print('Resource not found')
       elif error.status >= 500:
           print('Server error, please retry')
       else:
           print(f'Error: {error.message}')
    ''')

    print('✅ Example completed successfully!')

if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        print(f'❌ Error: {error}')
        exit(1)
