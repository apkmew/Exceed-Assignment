from fastapi import FastAPI, HTTPException, Body
from datetime import date
from pymongo import MongoClient
from pydantic import BaseModel
from dotenv import load_dotenv
import os
load_dotenv('.env')

user = os.getenv('user')
password = os.getenv('password')
DATABASE_NAME = "exceed04"
COLLECTION_NAME = "hotelMew"
MONGO_DB_URL = f"mongodb://{user}:{password}@mongo.exceed19.online:8443/?authMechanism=DEFAULT"
MONGO_DB_PORT = 8443


class Reservation(BaseModel):
    name : str
    start_date: date
    end_date: date
    room_id: int


client = MongoClient(f"{MONGO_DB_URL}")

db = client[DATABASE_NAME]

collection = db[COLLECTION_NAME]

app = FastAPI()


def room_avaliable(room_id: int, start_date: str, end_date: str):
    
    query={"room_id": room_id,
           "$or": 
                [{"$and": [{"start_date": {"$lte": start_date}}, {"end_date": {"$gte": start_date}}]},
                 {"$and": [{"start_date": {"$lte": end_date}}, {"end_date": {"$gte": end_date}}]},
                 {"$and": [{"start_date": {"$gte": start_date}}, {"end_date": {"$lte": end_date}}]}]
            }
    result = collection.find(query, {"_id": 0})
    list_cursor = list(result)
    return not len(list_cursor) > 0


@app.get("/reservation/by-name/{name}")
def get_reservation_by_name(name:str):
    results = []
    cursor = collection.find({"name": name}, {"_id": 0})
    for i in cursor:
        results.append(i)
    return {'result': results}

@app.get("/reservation/by-room/{room_id}")
def get_reservation_by_room(room_id: int):
    results = []
    cursor = collection.find({"room_id": room_id}, {"_id": 0})
    for i in cursor:
        results.append(i)
    return {'result': results}

@app.post("/reservation")
def reserve(reservation : Reservation):
    res = reservation.dict()
    res['start_date'] = str(res['start_date'])
    res['end_date'] = str(res['end_date'])
    roomCheck = 1 <= res['room_id'] <= 10
    dateCheck = res['start_date'] <= res['end_date']
    if roomCheck and dateCheck and room_avaliable(res['room_id'], res['start_date'], res['end_date']):
        collection.insert_one(res)
        return 'success reserving'
    else:
        raise HTTPException(status_code=400, detail="Invalid reservation")

@app.put("/reservation/update")
def update_reservation(reservation: Reservation, new_start_date: date = Body(), new_end_date: date = Body()):
    res = reservation.dict()
    res['start_date'] = str(res['start_date'])
    res['end_date'] = str(res['end_date'])
    new_start_date = str(new_start_date)
    new_end_date = str(new_end_date)
    dateCheck = new_start_date <= new_end_date
    if dateCheck and room_avaliable(res['room_id'], new_start_date, new_end_date):
        collection.update_one(res, {"$set": {"start_date": new_start_date, "end_date": new_end_date}})
        return 'success updating'
    else:
        raise HTTPException(status_code=400, detail="Invalid reservation")

@app.delete("/reservation/delete")
def cancel_reservation(reservation: Reservation):
    res = reservation.dict()
    res['start_date'] = str(res['start_date'])
    res['end_date'] = str(res['end_date'])
    collection.delete_one(res)
    return 'success deleting'