import datetime
from pymongo import MongoClient
import certifi

# 1. MongoDB Atlasへの接続設定
# ※ <username> と <password>、およびURLは自分のAtlasのものに書き換えてください
MONGO_URL = "mongodb+srv://matio:<db_password>@cluster0.metlisb.mongodb.net/?appName=Cluster0"

try:
    
    # クライアントの作成
    client = MongoClient(MONGO_URL, tlsCAFile=certifi.where())
    
    # 「vocab_db」という名前のデータベースを取得（なければ自動作成される）
    db = client["vocab_db"]
    
    # 「cards」という名前のコレクション（テーブル）を取得
    cards_collection = db["cards"]

    print("✅ MongoDBへの接続に成功しました！")

    # 2. テスト用単語データの定義（JSON形式風の辞書型）
    test_card = {
        "word": "ubiquitous",
        "meaning": "至る所にある、偏在する",
        "box_level": 1,
        "next_review": datetime.datetime.now() + datetime.timedelta(days=1),
        "created_at": datetime.datetime.now()
    }

    # 3. データベースへの保存（インサート）
    result = cards_collection.insert_one(test_card)
    print(f"💾 データを1件保存しました。生成されたID: {result.inserted_id}")

    # 4. 保存されたデータの確認（検索）
    saved_card = cards_collection.find_one({"word": "ubiquitous"})
    print("\n--- DBから取得したデータ ---")
    print(f"単語: {saved_card['word']}")
    print(f"意味: {saved_card['meaning']}")
    print(f"次回復習: {saved_card['next_review']}")

except Exception as e:
    print(f"❌ エラーが発生しました: {e}")