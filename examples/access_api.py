import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from onlyfans_sdk import OFAuthClient, self as self_api, posts, earnings, subscribers, subscriptions

load_dotenv()

def main():
    api_key = os.getenv('OFAUTH_API_KEY')
    connection_id = os.getenv('OFAUTH_CONNECTION_ID')

    if not api_key:
        raise ValueError('OFAUTH_API_KEY environment variable is required')
    if not connection_id:
        raise ValueError('OFAUTH_CONNECTION_ID environment variable is required for access API examples')

    client = OFAuthClient(api_key=api_key, connection_id=connection_id)

    print('🔑 OFAuth SDK - Access API Example\n')
    print(f'Using connection: {connection_id}\n')

    print('1. Getting creator profile...')
    profile = self_api.list_selfs(client, connection_id=connection_id)
    print(f'   ✓ Username: @{profile["username"]}')
    print(f'   ✓ Name: {profile.get("name", "N/A")}')
    print(f'   ✓ User ID: {profile["id"]}')
    print()

    print('2. Listing recent posts...')
    posts_list = posts.list_posts(client, connection_id=connection_id, limit=5)
    print(f'   ✓ Found {len(posts_list["list"])} posts')
    
    for post in posts_list['list']:
        text = post.get('text', '[No text]')
        preview = text[:50] if text else '[No text]'
        suffix = '...' if text and len(text) > 50 else ''
        print(f'   - Post {post["id"]}: {preview}{suffix}')
    print()

    print('3. Getting earnings data...')
    now = datetime.now()
    thirty_days_ago = now - timedelta(days=30)
    
    earnings_data = earnings.get_earnings_chart(
        client,
        connection_id=connection_id,
        start_date=thirty_days_ago.strftime('%Y-%m-%d'),
        end_date=now.strftime('%Y-%m-%d'),
    )
    
    print(f'   ✓ Data points: {len(earnings_data["chart"])}')
    if earnings_data['chart']:
        total = sum(point.get('amount', 0) for point in earnings_data['chart'])
        print(f'   ✓ Total earnings: ${total / 100:.2f}')
    print()

    print('4. Listing subscribers...')
    subs = subscribers.list_subscribers(
        client,
        connection_id=connection_id,
        limit=10,
        type='active',
    )
    print(f'   ✓ Found {len(subs["list"])} active subscribers (showing first page)')
    print(f'   ✓ Has more: {"Yes" if subs["hasMore"] else "No"}')
    print()

    print('5. Getting subscription counts...')
    counts = subscriptions.get_subscriptions_count(client, connection_id=connection_id)
    active_subs = counts.get('subscriptions', {}).get('active', 0)
    active_subscribers = counts.get('subscribers', {}).get('active', 0)
    print(f'   ✓ Active subscriptions: {active_subs}')
    print(f'   ✓ Active subscribers: {active_subscribers}')
    print()

    print('✅ Example completed successfully!')

if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        print(f'❌ Error: {error}')
        exit(1)
