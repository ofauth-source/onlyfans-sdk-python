import os
from dotenv import load_dotenv
from onlyfans_sdk import OFAuthClient, account

load_dotenv()

def main():
    api_key = os.getenv('OFAUTH_API_KEY')
    if not api_key:
        raise ValueError('OFAUTH_API_KEY environment variable is required')

    client = OFAuthClient(api_key=api_key)

    print('🔑 OFAuth SDK - Pagination Example\n')

    print('1. Using generator (automatic pagination)...')
    print('   Fetching first 25 connections...\n')
    
    count = 0
    for connection in account.iter_connections(client, max_items=25):
        count += 1
        username = connection['userData']['username']
        status = connection['status']
        print(f'   {count}. {connection["id"]} - {username} ({status})')
    
    print(f'\n   ✓ Fetched {count} connections total\n')

    print('2. Manual pagination with offset...')
    
    page = 1
    has_more = True
    offset = 0
    total_fetched = 0

    while has_more and page <= 3:
        print(f'\n   Fetching page {page}...')
        
        result = account.list_connections(
            client,
            limit=10,
            offset=offset,
        )
        
        print(f'   ✓ Got {len(result["list"])} connections')
        total_fetched += len(result['list'])
        
        has_more = result['hasMore']
        offset = offset + 10 if has_more else offset
        page += 1
    
    print(f'\n   ✓ Total fetched across {page - 1} pages: {total_fetched} connections\n')

    print('3. Custom page size with generator...')
    print('   Using page_size=5, max_items=15\n')
    
    count = 0
    pages_fetched = 0
    
    for connection in account.iter_connections(client, max_items=15, page_size=5):
        count += 1
        if count % 5 == 1:
            pages_fetched += 1
            print(f'   Page {pages_fetched}:')
        print(f'     - {connection["userData"]["username"]}')
    
    print(f'\n   ✓ Fetched {count} items across ~{pages_fetched} pages\n')

    print('✅ Example completed successfully!')

if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        print(f'❌ Error: {error}')
        exit(1)
