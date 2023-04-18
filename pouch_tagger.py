import json
import os
import requests
import config
from config import SHOPIFY_API_BASE_URL

session = requests.Session()
session.auth = config.auth

def get_pouch_count(product_id, variant_id=None):
    metafields = []

    if variant_id:
        # Fetch metafield data for the variant
        response = session.get(f'{SHOPIFY_API_BASE_URL}/variants/{variant_id}/metafields.json')
        metafields = response.json()['metafields']
        print(f"Metafields for product_id={product_id}, variant_id={variant_id}: {metafields}")

    # If no variant-level metafields found, or no variant ID was provided, fetch metafield data for the product
    if not metafields or not variant_id:
        response = session.get(f'{SHOPIFY_API_BASE_URL}/products/{product_id}/metafields.json')
        metafields = response.json()['metafields']
        print(f"Metafields for product_id={product_id}: {metafields}")

    print(f"API response status code: {response.status_code}")
    print(f"API response content: {response.content}")

    # Look for the 'Number of Pouches' metafield and return its value
    for metafield in metafields:
        if metafield['namespace'] == 'custom' and metafield['key'] == 'number_of_pouches':
            pouch_count = int(metafield['value'])  # Explicitly convert the value to an integer
            print(f"Found pouch count for product_id={product_id}, variant_id={variant_id}: {pouch_count}")
            return pouch_count

    return 0


def tag_order(order_id, tag):
    # Update the order with the new tag
    order = session.get(f'{SHOPIFY_API_BASE_URL}/orders/{order_id}.json').json()['order']
    order_tags = order.get('tags', '')
    if order_tags:
        new_tags = f'{order_tags}, {tag}'
    else:
        new_tags = tag

    order_update_data = {
        'order': {
            'id': order_id,
            'tags': new_tags
        }
    }
    session.put(f'{SHOPIFY_API_BASE_URL}/orders/{order_id}.json', json=order_update_data)

def lambda_handler(event, context):
    # Parse the webhook data from the event
    webhook_data = json.loads(event['body'])

    print("Webhook data:", webhook_data)

    # Calculate the total number of pouches in the order
    total_pouches = 0
    for item in webhook_data['line_items']:
        pouch_count = get_pouch_count(item['product_id'], item.get('variant_id', None))
        total_pouches += pouch_count * item['quantity']

    # Determine the appropriate tag for the order and update the order
    order_id = webhook_data['id']
    if total_pouches <= 3:
        tag_order(order_id, 'Gnome-UPS')
    else:
        tag_order(order_id, 'Normal-UPS')

    return {
        'statusCode': 200,
        'body': json.dumps('Order tagged successfully'),
    }
