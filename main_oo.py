import json
from typing import List, Tuple, Optional

import requests

class Fulcrum:
    def __init__(self, bear_token: str):
        self.bear_token = bear_token
        self.base_url = "https://api.fulcrumpro.com/api/"

    def findQuote(self, quoteNumber: int):
        """Find quote given the quote number in fulcrum"""
        request = requests.post(
            self.base_url + "/quotes/list",
            headers={'Authorization': f'Bearer {self.bear_token}'},
            json={
                "numbers": [quoteNumber]
            }
        )
        return request.json()

    def getQuote(self, quoteID: str):
        """Get quote given the quoteID from Fulcrum's backend"""
        request = requests.get(
            self.base_url + f"/quotes/{quoteID}",
            headers={'Authorization': f'Bearer {self.bear_token}'},
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
            headers={'Authorization': f'Bearer {self.bear_token}'},
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
            headers={'Authorization': f'Bearer {self.bear_token}'}
        )
        return res.json()

    def getRoutingIDs(self, quoteID: str, lineItemID: str) -> list:
        """Get route IDs (manufacturing process schema) for a given part (line item) and quote"""
        res = requests.get(
            self.base_url + f"/quotes/{quoteID}/part-line-items/{lineItemID}/make-summary",
            headers={'Authorization': f'Bearer {self.bear_token}'}
        )
        return [i['routingId'] for i in res.json()]

    def getInputMaterials(self, quoteID: str, lineItemID: str, routingID: str) -> list:
        """Get input materials to consist a part, given quote, part (line item) and routing ID"""
        res = requests.post(
            self.base_url + f"/quotes/{quoteID}/part-line-items/{lineItemID}/routing/{routingID}/input-materials/list",
            headers={'Authorization': f'Bearer {self.bear_token}'}
        )
        return res.json()

    def getVendorName(self, vendorID: str) -> str:
        """Get vendor name from vendorID"""
        res = requests.get(
            self.base_url + f"/vendors/{vendorID}",
            headers={'Authorization': f'Bearer {self.bear_token}'}
        )
        return res.json()['name']

    def getMaterial(self, materialID: str) -> str:
        res = requests.post(
            self.base_url + f"/materials/list", #{materialID}",
            headers={'Authorization': f'Bearer {self.bear_token}'},
            json={'ids': [materialID]}
        )
        return res.json()[0]

class FulcrumObject:
    fulcrum: Fulcrum | None = None

    @classmethod
    def init_fulcrum(cls):
        if cls.fulcrum is None:
            bearer_token = open('api_key.txt').read().strip()
            cls.fulcrum = Fulcrum(bearer_token)

class Quote(FulcrumObject):
    def __init__(self, quoteNumber: int):
        self.quoteID : str = self.fulcrum.getQuoteID(quoteNumber)

        assembly = self.fulcrum.getParts(self.quoteID)
        self.assembly : List[Part]= [Part(i['id'], self.quoteID) for i in assembly]

        self.materials : List[MaterialNeeded]= []

class Part(FulcrumObject):
    def __init__(self, partID: str, quoteID: Optional[str] = None):
        self.partID : str = partID
        self.quoteID : Optional[str] = quoteID


        self.subparts : List[Subpart]= [
            Subpart(i, partID=self.partID, quoteID=self.quoteID)
            for i
            in self.fulcrum.getRoutingIDs(self.quoteID, self.partID)
        ]  # routingIDs

        self.materials : List[MaterialNeeded]= []
        for subpart in self.subparts:
            self.materials.append(subpart.material)
        a =1

class Subpart(FulcrumObject):
    def __init__(self, subpartID: str, partID: Optional[str] = None, quoteID: Optional[str] = None):
        self.subpartID : str = subpartID
        self.material : MaterialNeeded = None
        self.dimensions : Tuple[int, int] = 0, 0

        self.partID : Optional[str] = partID
        self.quoteID : Optional[str] = quoteID

        material_list = self.fulcrum.getInputMaterials(
            quoteID=self.quoteID,
            lineItemID=self.partID,
            routingID=self.subpartID
        )
        if material_list:
            print(json.dumps(material_list, indent=2))
        for mat in material_list:
            mshape = mat['materialShape']
            a = Material(
                mat['materialId'],
            )
        b = 1

class Material(FulcrumObject):
    def __init__(self, materialNameID: str):
        """
        :param materialNameID: i.e. SS-304-#4|SS-304-#4-Sheet-0.06
        """
        self.materialID : str = materialNameID
        mat = self.fulcrum.getMaterial(self.materialID)  # TEMP
        # mshape = mat['materialShape']

        self.materialName : str = mat['materialReferenceId']  # i.e. SS-304

        self.fulcrum.getMaterial(self.materialID)
        self.materialForm = mat['form'],
        self.materialType = mat['materialReferenceName'],  # Stainless steel, aluminum, etc
        self.thickness = mat['dimension'].replace('"', 'in'),
        self.vendor = self.fulcrum.getVendorName(mat['vendors'][0]['vendorId'])  # TODO: make this parse a list of vendors
        a = 1

class MaterialNeeded(Material):
    def __init__(self, materialNameID: str):
        """
        :param materialNameID: i.e. SS-304-#4|SS-304-#4-Sheet-0.06
        """
        super().__init__(materialNameID)
        self.dimensions : Tuple[int, int] | int = 0

        dimensions = (mat['nestings']['d2'], mat['nestings']['d3'])

        if self.materialType == 'roundBar':
            self.dimensions = 1
        elif self.materialType == 'sheet':
            self.dimensions = (1, 1)


FulcrumObject.init_fulcrum()
Quote(1050)