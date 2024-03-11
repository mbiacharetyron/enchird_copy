import requests, json, pprint
from django.conf import settings
from requests.auth import HTTPBasicAuth



def get_paypal_access_token(client_id, client_secret):
    # PayPal OAuth 2.0 Token Endpoint
    token_url = settings.AUTH_URL

    # PayPal API credentials
    auth = HTTPBasicAuth(client_id, client_secret)

    # Token request payload
    data = {
        'grant_type': 'client_credentials'
    }

    # Make the request to obtain the access token
    response = requests.post(token_url, auth=auth, data=data)

    if response.status_code == 200:
        # Parse the JSON response to extract the access token
        access_token = response.json().get('access_token')
        return access_token
    else:
        # Print the error details if the request fails
        print(f"Failed to get access token. Status code: {response.status_code}")
        print(response.text)
        return None
    
    
    
def create_paypal_order(user, client_id, client_secret, amount, return_url, cancel_url, currency='USD'):
    # PayPal API credentials
    auth = HTTPBasicAuth(client_id, client_secret)

    # PayPal Orders API endpoint
    orders_url = settings.ORDER_URL

    # Order creation payload
    data = {
        "intent": "CAPTURE",
        "purchase_units": [
            {
                "items": [
                    {
                        "name": f"{user.first_name} {user.last_name} - Enchird Fee Payment",
                        "description": user.email,
                        "quantity": "1",
                        "unit_amount": {
                            "currency_code": currency,
                            "value": str(amount)
                        }
                    }
                ],
                "amount": {
                    "currency_code": currency,
                    "value": str(amount),
                    "breakdown": {
                        "item_total": {
                            "currency_code": currency,
                            "value": str(amount)
                        }
                    }
                },
            }
        ],
        "application_context": {
            "return_url": return_url,
            "cancel_url": cancel_url
        }
    }

    # Make the request to create the order
    response = requests.post(orders_url, auth=auth, json=data, headers={'Content-Type': 'application/json'})
    print(response)
    response_data = response.json()
    print(response_data)
    

    return response



def check_paypal_order(client_id, client_secret, order_id):
    auth = HTTPBasicAuth(client_id, client_secret)
    orders_url = f'https://api-m.sandbox.paypal.com/v2/checkout/orders/{order_id}'
    
    response = requests.get(orders_url, auth=auth, headers={'Content-Type': 'application/json'})

    return response

    # if response.status_code == 200:
    #     order_details = response.json()
    #     print("Order Details:")
    #     print(order_details)
    #     return order_details
    # elif response.status_code == 404:
    #     print(f"Order with ID {order_id} not found.")
    #     return None
    # else:
    #     print(f"Failed to retrieve order details. Status code: {response.status_code}")
    #     return None


    