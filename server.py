from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import uvicorn

app = FastAPI(title="Information System API")

# Модель данных
class Item(BaseModel):
    id: Optional[int] = None
    title: str
    description: str
    status: str = "active"

# Временное хранилище данных (в памяти)
db = [
    {"id": 1, "title": "Пример задачи 1", "description": "Описание первой задачи", "status": "active"},
    {"id": 2, "title": "Пример задачи 2", "description": "Описание второй задачи", "status": "completed"}
]
item_id_counter = 3

@app.get("/items", response_model=List[Item])
async def get_items():
    """Получение всех элементов"""
    return db

@app.get("/items/{item_id}", response_model=Item)
async def get_item(item_id: int):
    """Получение одного элемента по ID"""
    item = next((item for item in db if item["id"] == item_id), None)
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return item

@app.post("/items", response_model=Item)
async def create_item(item: Item):
    """Создание нового элемента"""
    global item_id_counter
    new_item = item.dict()
    new_item["id"] = item_id_counter
    db.append(new_item)
    item_id_counter += 1
    return new_item

@app.delete("/items/{item_id}")
async def delete_item(item_id: int):
    """Удаление элемента"""
    global db
    item = next((item for item in db if item["id"] == item_id), None)
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    db = [i for i in db if i["id"] != item_id]
    return {"message": "Item deleted successfully"}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
