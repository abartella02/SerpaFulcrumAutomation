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

    def getMaterial(self, materialID: str) -> dict:
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

        self.materialNeeded = {}

        for i in self.assembly:
            for key, value in i.materialNeeded.items():
                if self.materialNeeded.get(key, None) is None:
                    self.materialNeeded[key] = value
                else:
                    self.materialNeeded[key] += value

    def getMaterialNeeded(self):
        return self.materialNeeded

class Part(FulcrumObject):
    def __init__(self, partID: str, quoteID: Optional[str] = None):
        self.partID : str = partID
        self.quoteID : Optional[str] = quoteID


        self.routings : List[Routing]= [
            Routing(i, partID=self.partID, quoteID=self.quoteID)
            for i
            in self.fulcrum.getRoutingIDs(self.quoteID, self.partID)
        ]  # routingIDs

        self.materialNeeded = {}
        for subpart in self.routings:
            # self.materials.append(subpart.materialNeeded)
            # a = subpart.material
            for i in subpart.material:
                if self.materialNeeded.get(i.materialID, None) is None:
                    if i.materialForm == 'roundBar':
                        self.materialNeeded[i.materialID] = i.dimensions[0]
                    else:
                        self.materialNeeded[i.materialID] = i.area
                else:
                    if i.materialForm == 'roundBar':
                        self.materialNeeded[i.materialID] += i.dimensions[0]
                    else:
                        self.materialNeeded[i.materialID] += i.area

class Routing(FulcrumObject):
    def __init__(self, routingID: str, partID: Optional[str] = None, quoteID: Optional[str] = None):
        self.routingID : str = routingID
        # self.material : List[MaterialNeeded] = []
        self.dimensions : Tuple[int, int] = 0, 0

        self.partID : Optional[str] = partID
        self.quoteID : Optional[str] = quoteID

        material_list = self.fulcrum.getInputMaterials(
            quoteID=self.quoteID,
            lineItemID=self.partID,
            routingID=self.routingID
        )

        self.material = []
        for mat in material_list:
            self.material.append(MaterialNeeded(mat['materialId'], mat['materialShape'], mat['nestings']))


class Material(FulcrumObject):
    def __init__(self, materialNameID: str, materialShape: dict):
        """
        :param materialNameID: i.e. SS-304-#4|SS-304-#4-Sheet-0.06 (called materialID in api response)
        """
        self.materialID : str = materialNameID
        mat : dict = self.fulcrum.getMaterial(self.materialID)
        matShape: dict = materialShape

        self.materialName : str = mat['materialReferenceId']  # i.e. SS-304

        # self.fulcrum.getMaterial(self.materialID)
        self.materialForm : str = matShape['form']  # Roundbar, sheet
        self.materialType : str = matShape['materialReferenceName']  # Stainless steel, aluminum, etc
        self.thickness : str = matShape['dimension'].replace('"', 'in')  # 12 GA, 0.25", etc
        self.vendors : list[Vendor] = [Vendor(vendor['vendorId']) for vendor in matShape['vendors']]

class Vendor (FulcrumObject):
    # TODO
    def __init__(self, vendorID: str):
        self.vendorID : str = vendorID

class MaterialNeeded(Material):
    def __getDims(self, nestings: dict) -> Tuple:
        d1 = nestings.get('d1', None)
        d2 = nestings.get('d2', None)
        d3 = nestings.get('d3', None)
        if all([d1, d2, d3]):
            dimensions = (d1, d2, d3)
        elif d1 and d2:
            dimensions = (d1, d2)
        elif d1 and d3:
            dimensions = (d1, d3)
        elif d2 and d3:
            dimensions = (d2, d3)
        elif d1:
            dimensions = (d1,)
        elif d2:
            dimensions = (d2,)
        elif d3:
            dimensions = (d3,)
        else:
            raise ValueError(f'No dimensions found for material {self.materialID}')
        return dimensions

    def __init__(self, materialNameID: str, materialShape : dict, nestings : dict):
        """
        :param materialNameID: i.e. SS-304-#4|SS-304-#4-Sheet-0.06 (called materialID in api response)
        :param nestings: dict of dimensions of part
        """
        self.material = super().__init__(materialNameID, materialShape)
        self._dimensions : Tuple[int] = self.__getDims(nestings[0])
        self.dimensions : Tuple[int, int] | Tuple[int] | None = None
        self.area : int = 0  # in square inches

        if self.materialForm == 'roundBar':
            self.dimensions = self._dimensions[0],  # x in inches
        elif self.materialForm == 'sheet' and len(self._dimensions) >= 2:
            self.dimensions = self._dimensions  # x, y in inches
            self.area = self._dimensions[0] * self._dimensions[1]
        # print("**", self.materialName, self.materialForm, self.dimensions, self.area)

FulcrumObject.init_fulcrum()
a = Quote(1050)
print(json.dumps(a.materialNeeded, indent=2))