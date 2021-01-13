import requests

from typing import List
from pydantic import BaseModel

from fastapi import APIRouter

root = APIRouter()
SHOPDB = "https://api.steinhq.com/v1/storages/5fff0e51f62b6004b3eb64e8"

class Data(BaseModel):
    question: str
    created: str

class Sessions(BaseModel):
    data: List[Data]

'''
{
    data: [
        {
            question: "items",
            created: timestamp.
        }
    ]
}
'''

@root.get("/")
async def hello():
    return {"message": "Hello World"}

@root.post("/")
async def helloPost(data: Sessions):
    return {"message": f"Hello World the request query is *{data.data[0].question}* at {data.data[0].created}"}

@root.post("/item/list")
async def listOfItems():
    products = requests.get(f"{SHOPDB}/product")
    if products.status_code != 200:
        return {"message": "Hey The AWESOME SHOP is kind offline, so come back later"}
    itemLists = products.json()
    wordItemLists = ""
    for index, item in enumerate(itemLists):
        wordItemLists += f"{index+1}. {item['name']} Rp. {item['price']} [{item['code']}]\n"
    return {"message": f"Hello and Welcome to my AWESOME SHOP\n\n"
                       "Here is our available product:\n"
                       f"{wordItemLists}\n"
                       "to buy you can use the command *buy PRODUCT_CODE 2*"}