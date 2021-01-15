import requests

from datetime import date
from typing import List
from pydantic import BaseModel

from fastapi import APIRouter

root = APIRouter()
SHOPDB = "https://api.steinhq.com/v1/storages/5fff0e51f62b6004b3eb64e8"
RAJAONGKIR_API = "https://api.rajaongkir.com/starter"

class Data(BaseModel):
    slug: str
    question: str
    answer: str
    created: str

class Sessions(BaseModel):
    phone_number: str
    data: List[Data]
    current_process: str
    current_question_slug: str
    process_status: str
    created: str


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

def shippingCost(frm: str, to: str, weight: int) -> str:
    getCity = requests.get(f"{RAJAONGKIR_API}/city", headers={'key': '7d0822225707090f23a77dceecf97e6c'})
    cities = getCity.json()['rajaongkir']['results']
    cityName = [item['city_name'].lower() for item in cities]
    
    frmID = cities[cityName.index(frm.lower())]['city_id']
    toID = cities[cityName.index(to.lower())]['city_id']

    getCost = requests.post(f"{RAJAONGKIR_API}/cost", json={
        'key':'7d0822225707090f23a77dceecf97e6c',
        'origin': frmID,
        'destination': toID,
        'weight': weight,
        'courier': 'jne'
    })

    print(getCost.status_code)
    if getCost.status_code == 200:
        return getCost.json()['rajaongkir']['results'][0]['costs'][1]['cost'][0]['value']
    return getCost.status_code

@root.get("/")
async def hello():
    return {"message": "Hello World"}

@root.post("/")
async def helloPost(data: Sessions):
    return {"message": f"Hello World the request query is *{data.data[0].question}* at {data.data[0].created}"}

@root.post("/item/list")
async def listOfItems():
    products = requests.get(f"{SHOPDB}/products")
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


@root.post("/buy")
async def searchItems(data: Sessions):
    getConfig = requests.get(f'{SHOPDB}/configs')
    config = getConfig.json()
    getCustomer = requests.get(f'{SHOPDB}/customers?search={{"phone_number":"{data.phone_number}"}}')
    if getCustomer.status_code != 200:
        return {"message": "Hey The AWESOME SHOP is kind offline, so come back later"}
    customer = getCustomer.json()
    if len(customer) <= 0:
        return {"message": f"your phone number {data.phone_number} is not registered,\n"
                            "you can regsitered first with the command *register*"}
    
    products = requests.get(f'{SHOPDB}/products?search={{"code":"{data.data[0].question}"}}')
    if products.status_code != 200:
        return {"message": "Hey The AWESOME SHOP is kind offline, so come back later"}

    item = products.json()
    shipping_cost = shippingCost(config[0]['shop_city'], customer[0]['city'], int(item[0]['weight']))
    newTrx = {
        'code_product': item[0]['code'], 
        'code_cust': customer[0]['code_cust'],
        'qty': '1',
        'sum': shipping_cost,
        'total': int(shipping_cost) + int(item[0]['price']),
        'status': 'ORDERED',
        'date_ordered': date.today().strftime("%d/%m/%Y")
    }
    addNewTransaction = requests.post(f'{SHOPDB}/transactions', json=[newTrx])

    return {"message": f"Hello *{customer[0]['name']}* you want to buy *{item[0]['name']}* \n"
                       f"With price *{item[0]['price']}*\n"
                       f"the size of the product is *{item[0]['weight']}* *{item[0]['weight_uom']}*\n\n"
                       f"with the JNE Regular from *{config[0]['shop_city']}* to *{customer[0]['city']}*\n"
                       f"you need to pay extra *{shipping_cost}* for shipping cost\n\n"
                       f"with Total: *Rp.{newTrx['total']}*"
                       "\n\nyou need to pay to this bank number dude"}

@root.post("/register")
async def register(data: Sessions):
    getCustomer = requests.get(f'{SHOPDB}/customers?search={{"phone_number":"{data.phone_number}"}}')
    if getCustomer.status_code != 200:
        return {"message": "Hey The AWESOME SHOP is kind offline, so come back later"}
    customer = getCustomer.json()
    if len(customer) <= 0:
        addNewCustomer = requests.post(f'{SHOPDB}/customers',json=[
            {
                'phone_number': data.phone_number, 
                'name': data.data[0].answer,
                'code_cust': f"{data.data[0].answer[0:3].upper()}{data.phone_number[round(len(data.phone_number)/2):round(len(data.phone_number)/2)+3].upper()}"
            }])
        print(addNewCustomer.status_code)
        return addNewCustomer.status_code
    print(data.data[-1].slug)
    updateCustomer = requests.put(f'{SHOPDB}/customers', json={
            'condition': {'phone_number': f"{data.phone_number}"},
            'set': {f"{data.data[-1].slug}": f"{data.data[-1].answer}"}
    })
    print(updateCustomer.status_code)
    print(updateCustomer.text)
    return updateCustomer.status_code