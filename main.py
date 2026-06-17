import os

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pymongo import MongoClient
from pydantic import BaseModel
from bson import ObjectId
from datetime import datetime, timedelta, timezone

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

@app.get("/", response_class=HTMLResponse)
def read_index():
    # index.html の中身を読み込んで、そのままブラウザに生HTMLとして返す
    with open("index.html", "r", encoding="utf-8") as f:
        return f.read()


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
            "box_level": new_level,
            "last_reviewed_at": datetime.now(timezone.utc)
        }
    }
    cards_collection.update_one(query, new_values)
    
    return {
        "status": "success",
        "message": message,
        "current_level": new_level
    }


@app.get("/cards/quiz")
def get_quiz_card():
    now = datetime.now(timezone.utc)
    
    all_cards = list(cards_collection.find())
    
    due_cards = []
    
    for card in all_cards:
        card["id"] = str(card["_id"])
        del card["_id"]
        
        if card.get("box_level", 0) == 0:
            due_cards.append(card)
            continue
            
        last_reviewed = card.get("last_reviewed_at")
        if not last_reviewed:
            due_cards.append(card)
            continue
            
        if last_reviewed.tzinfo is None:
            last_reviewed = last_reviewed.replace(tzinfo=timezone.utc)
            
        elapsed_time = now - last_reviewed
        box_level = card.get("box_level", 1)
        
        if box_level == 1:
            interval = timedelta(days=1)
        elif box_level == 2:
            interval = timedelta(days=3)
        elif box_level == 3:
            interval = timedelta(days=7)
        else:
            interval = timedelta(days=14)
            
        if elapsed_time >= interval:
            due_cards.append(card)
            
    if not due_cards:
        return {"message": "今日の復習はすべて完了しました！素晴らしい！", "card": None}
    return {"message": "クイズの時間です！", "card": due_cards[0]}