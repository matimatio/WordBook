import os

from fastapi import FastAPI
from pymongo import MongoClient
from pydantic import BaseModel
from bson import ObjectId

app = FastAPI()


MONGO_URL = os.getenv("MONGODB_URL")
client = MongoClient(MONGO_URL)

db = client["vocab_db"]
cards_collection = db["cards"]

#http://127.0.0.1:8000/docs

# ==========================================
# 1. 画面から送られてくるデータの「形（型）」の定義
# ==========================================
class CardCreate(BaseModel):
    word: str
    meaning: str

class CardUpdate(BaseModel):
    word: str
    meaning: str
    box_level: int

class CardReview(BaseModel):
    is_correct: bool

# ==========================================
# 2. 各種 窓口（APIエンドポイント）の定義
# ==========================================

@app.get("/")
def read_root():
    return {"message": "単語帳アプリのバックエンドサーバーが起動中！"}


@app.get("/cards")
def get_all_cards():
    cards = []
    for card in cards_collection.find():
        cards.append({
            "id": str(card["_id"]),
            "word": card["word"],
            "meaning": card["meaning"],
            "box_level": card["box_level"]
        })
    return {"status": "success", "data": cards}


@app.post("/cards")
def create_card(card_data: CardCreate):
    new_card = {
        "word": card_data.word,
        "meaning": card_data.meaning,
        "box_level": 1  
    }
    
    result = cards_collection.insert_one(new_card)
    
    return {
        "status": "success",
        "message": "単語が新しく登録されました！",
        "card_id": str(result.inserted_id)
    }


@app.delete("/cards/{card_id}")
def delete_card(card_id: str):
    query = {"_id": ObjectId(card_id)}
    
    result = cards_collection.delete_one(query)
    
    if result.deleted_count == 0:
        return {"status": "error", "message": "指定された単語が見つかりませんでした。"}
        
    return {"status": "success", "message": "単語を正常に削除しました！"}


@app.put("/cards/{card_id}")
def update_card(card_id: str, card_data: CardUpdate):
    query = {"_id": ObjectId(card_id)}

    new_values = {
        "$set":{
            "word": card_data.word,
            "meaning": card_data.meaning,
            "box_level": card_data.box_level
        }
    }

    result = cards_collection.update_one(query, new_values)

    if result.matched_count == 0:
        return {"status": "error", "message": "指定された単語が見つかりませんでした。"}
        
    return {"status": "success", "message": "単語の情報を更新しました。"}


@app.put("/cards/{card_id}/review")
def review_card(card_id: str, review_data: CardReview):
    query = {"_id": ObjectId(card_id)}
    
    current_card = cards_collection.find_one(query)
    if not current_card:
        return {"status": "error", "message": "指定された単語が見つかりませんでした。"}
    
    current_level = current_card.get("box_level", 1)
    
    if review_data.is_correct:
        new_level = min(current_level + 1, 5)
        message = f"正解！レベルが {current_level} から {new_level} に上がりました。"
    else:
        new_level = 1
        message = "不正解…！レベル1にリセットされました。復習しましょう！"

    new_values = {
        "$set": {
            "box_level": new_level
        }
    }
    cards_collection.update_one(query, new_values)
    
    return {
        "status": "success",
        "message": message,
        "current_level": new_level
    }