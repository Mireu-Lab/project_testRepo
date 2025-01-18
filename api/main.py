import sqlite3
from fastapi import FastAPI, HTTPException, status
from typing import List, Optional
from pydantic import BaseModel, Field

app = FastAPI()

# Pydantic model for a TODO item
class TodoItem(BaseModel):
    id: Optional[int] = None  #id는 자동으로 생성될 수 있으므로 Optional로 설정
    title: str = Field(..., min_length=1, max_length=100)
    completed: bool = False

# Database setup (creates table if it doesn't exist)
conn = sqlite3.connect('todo.db')
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS todos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        completed INTEGER DEFAULT 0  -- 0 for False, 1 for True
    )
''')
conn.commit()


# API endpoints

@app.post("/todos/", response_model=TodoItem, status_code=status.HTTP_201_CREATED)
async def create_todo(todo: TodoItem):
    cursor.execute(f"INSERT INTO todos (title, completed) VALUES ({todo.title}, {todo.completed})")
    conn.commit()
    cursor.execute("SELECT last_insert_rowid()")
    todo.id = cursor.fetchone()[0]
    return todo


@app.get("/todos/", response_model=List[TodoItem])
async def read_todos():
    cursor.execute("SELECT id, title, completed FROM todos")
    rows = cursor.fetchall()
    todos = [TodoItem(id=row[0], title=row[1], completed=bool(row[2])) for row in rows]
    return todos


@app.get("/todos/{todo_id}", response_model=TodoItem)
async def read_todo(todo_id: int):
    cursor.execute(f"SELECT id, title, completed FROM todos WHERE id = {todo_id}")
    row = cursor.fetchone()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found")
    return TodoItem(id=row[0], title=row[1], completed=bool(row[2]))


@app.put("/todos/{todo_id}", response_model=TodoItem)
async def update_todo(todo_id: int, todo: TodoItem):
    cursor.execute(f"UPDATE todos SET title = {todo.title}, completed = {todo.completed} WHERE id = {todo_id}")
    conn.commit()
    if cursor.rowcount == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found")
    cursor.execute(f"SELECT id, title, completed FROM todos WHERE id = {todo_id}")
    row = cursor.fetchone()
    return TodoItem(id=row[0], title=row[1], completed=bool(row[2]))


@app.delete("/todos/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_todo(todo_id: int):
    cursor.execute(f"DELETE FROM todos WHERE id = {todo_id}")
    conn.commit()
    if cursor.rowcount == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found")

# Run the app
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)