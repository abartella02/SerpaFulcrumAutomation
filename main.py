import json
import requests

class Fulcrum:
    def __init__(self, bear_token: str):
        self.bear_token = bear_token
        self.base_url = "https://api.fulcrumpro.com/api/"

    def findQuote(self, quoteNumber: int):
        """Find quote given the quote number in fulcrum"""
        request = requests.post(
            self.base_url + "/quotes/list",
            headers={'Authorization': f'Bearer {bear_token}'},
            json={
                "numbers": [quoteNumber]
            }
        )
        return request.json()

    def getQuote(self, quoteID: str):
        """Get quote given the quoteID from Fulcrum's backend"""
        request = requests.get(
            self.base_url + f"/quotes/{quoteID}",
            headers={'Authorization': f'Bearer {bear_token}'},
        )
        return request.json()

    def getQuoteID(self, quoteNumber: int) -> str:
        """Get quote ID given the quote number from Fulcrum's backend"""
        quote = self.findQuote(quoteNumber)
        if len(quote) > 1:
            raise Exception("Error: more than one quote found")
        return quote[0]['id']

    def getParts(self, quoteID: str):
        """Get all parts consisting a given quote"""
        request = requests.post(
            self.base_url + f"/quotes/{quoteID}/part-line-items/list",
            headers={'Authorization': f'Bearer {bear_token}'},
        )
        return request.json()

    def getPartIDs(self, quoteID: str):
        """Get IDs of all parts consisting a given quote"""
        parts = self.getParts(quoteID)
        return [i.get('itemId') for i in parts]

    def getItem(self, itemID: str):
        """General: get item given item ID"""
        res = requests.get(
            self.base_url + f"/items/{itemID}",
            headers={'Authorization': f'Bearer {bear_token}'}
        )
        return res.json()

    def getRoutingIDs(self, quoteID: str, lineItemID: str) -> list:
        """Get route IDs (manufacturing process schema) for a given part (line item) and quote"""
        res = requests.get(
            self.base_url + f"/quotes/{quoteID}/part-line-items/{lineItemID}/make-summary",
            headers={'Authorization': f'Bearer {bear_token}'}
        )
        return [i['routingId'] for i in res.json()]

    def getInputMaterials(self, quoteID: str, lineItemID: str, routingID: str) -> list:
        """Get input materials to consist a part, given quote, part (line item) and routing ID"""
        res = requests.post(
            self.base_url + f"/quotes/{quoteID}/part-line-items/{lineItemID}/routing/{routingID}/input-materials/list",
            headers={'Authorization': f'Bearer {bear_token}'}
        )
        return res.json()

    def getVendorName(self, vendorID: str) -> str:
        """Get vendor name from vendorID"""
        res = requests.get(
            self.base_url + f"/vendors/{vendorID}",
            headers={'Authorization': f'Bearer {bear_token}'}
        )
        return res.json()['name']

bear_token = open('api_key.txt', 'r').read()
fulcrum = Fulcrum(bear_token)

quoteID = fulcrum.getQuoteID(1050)
parts = fulcrum.getParts(quoteID)
routingIDs = fulcrum.getRoutingIDs(quoteID, parts[0]['id'])

for part in parts:
    print(part['description'].split('\n')[0])
    print("******************")
    routingIDs = fulcrum.getRoutingIDs(quoteID, part['id'])
    materials = {}
    for routingID in routingIDs:
        mats = fulcrum.getInputMaterials(quoteID, part['id'], routingID)
        if mats:
            for m in mats:
                print(m['materialShape']['materialReferenceId'], m['materialShape']['dimension'])  # material codename and thickness
                print("vendor:", fulcrum.getVendorName(m['materialShape']['vendors'][0]['vendorId']))  # vendor name
                print("Price: ", m['materialShape']['vendors'][0]['priceBreaks'][0]['price'], '/lb')  # material price
                print(f"Dimensions: {m['nestings'][0]['d2']}\" x {m['nestings'][0]['d3']}\"")  # length and width of part

                # track total length and width of sheet metal needed
                # TODO: exclude roundbar from this check, make another process for roundbar
                if not materials.get(m['materialShape']['dimension'], None):
                    materials[m['materialShape']['dimension']] = [m['nestings'][0]['d2'], m['nestings'][0]['d3']]
                else:
                    materials[m['materialShape']['dimension']][0] += m['nestings'][0]['d2']
                    materials[m['materialShape']['dimension']][1] += m['nestings'][0]['d3']
            print()

    print("total sheet metal needed:", json.dumps(materials, indent=2))




# print(json.dumps(res.json(), indent=4))