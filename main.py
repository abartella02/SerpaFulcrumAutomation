import json
import requests

bear_token = open('api_key.txt', 'r').read()
base_url = 'https://api.fulcrumpro.com/api'

def getQuotes(quoteNumber: int):
    request = requests.post(
        base_url+"/quotes/list",
        headers={'Authorization': f'Bearer {bear_token}'},
        json={
            "numbers": [quoteNumber]
        }
    )
    return request.json()

def getQuote(quoteID: str):
    request = requests.get(
        base_url+f"/quotes/{quoteID}",
        headers={'Authorization': f'Bearer {bear_token}'},
    )
    return request.json()

def getQuoteID(quoteNumber: int) -> str:
    quote = getQuotes(quoteNumber)
    if len(quote) > 1:
        raise Exception("Error: more than one quote found")
    return quote[0]['id']

def getParts(quoteID: str):
    request = requests.post(
        base_url+f"/quotes/{quoteID}/part-line-items/list",
        headers={'Authorization': f'Bearer {bear_token}'},
    )
    return request.json()

def getPartIDs(quoteID: str):
    parts = getParts(quoteID)
    return [i.get('itemId') for i in parts]

def getItem(itemID: str):
    res = requests.get(
        base_url+f"/items/{itemID}",
        headers={'Authorization': f'Bearer {bear_token}'}
    )
    return res.json()

def getRoutingIDs(quoteID: str, lineItemID: str) -> list:
    res = requests.get(
        base_url + f"/quotes/{quoteID}/part-line-items/{lineItemID}/make-summary",
        headers={'Authorization': f'Bearer {bear_token}'}
    )
    return [i['routingId'] for i in res.json()]

def getInputMaterials(quoteID: str, lineItemID: str, routingID: str) -> list:
    res = requests.post(
        base_url + f"/quotes/{quoteID}/part-line-items/{lineItemID}/routing/{routingID}/input-materials/list",
        headers={'Authorization': f'Bearer {bear_token}'}
    )
    return res.json()

def getVendorName(vendorID: str) -> str:
    res = requests.get(
        base_url + f"/vendors/{vendorID}",
        headers={'Authorization': f'Bearer {bear_token}'}
    )
    return res.json()['name']

quoteID = getQuoteID(1050)
parts = getParts(quoteID)
routingIDs = getRoutingIDs(quoteID, parts[0]['id'])

for part in parts:
    print(part['description'].split('\n')[0])
    print("******************")
    routingIDs = getRoutingIDs(quoteID, part['id'])
    for routingID in routingIDs:
        mats = getInputMaterials(quoteID, part['id'], routingID)
        if mats:
            for m in mats:
                # print(json.dumps(m, indent=4))
                print(m['materialShape']['materialReferenceId'], m['materialShape']['dimension'])
                print("vendor:", getVendorName(m['materialShape']['vendors'][0]['vendorId']))
                print("Price: ", m['materialShape']['vendors'][0]['priceBreaks'][0]['price'], '/lb')
                print(f"Dimensions: {m['nestings'][0]['d2']}\" x {m['nestings'][0]['d3']}\"")
            print()

# print(json.dumps(res.json(), indent=4))