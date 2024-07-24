from fastapi import FastAPI, WebSocket, HTTPException
from pydantic import BaseModel
from typing import List
import databases
import sqlalchemy
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "postgresql+asyncpg://postgres:suaida@localhost/movie_db"

database = databases.Database(DATABASE_URL)
metadata = sqlalchemy.MetaData()

movies_table = sqlalchemy.Table(
    "movies",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True,autoincrement=True),
    sqlalchemy.Column("title", sqlalchemy.String(length=255)),
    sqlalchemy.Column("year", sqlalchemy.Integer),
)

engine = create_async_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

app = FastAPI()
websocket_connections = []

class Movie(BaseModel):
    title: str
    year: int

@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(metadata.create_all)
    await database.connect()

@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()

@app.get("/movies", response_model=List[Movie])
async def get_movies():
    query = movies_table.select()
    movies = await database.fetch_all(query)
    return [{"id": movie["id"], "title": movie["title"], "year": movie["year"]} for movie in movies]

@app.post("/movies", response_model=Movie)
async def create_movie(movie: Movie):
    query = movies_table.insert().values(title=movie.title, year=movie.year)
    last_record_id = await database.execute(query)
    movie_data = {
    "title": movie.title,
    "year": movie.year,
    "id": last_record_id
}
    print(f'Movie created: {movie_data}') 
    await notify_websockets(movie_data, "movie_created")
    return movie_data

@app.delete("/movies/{movie_id}", response_model=Movie)
async def delete_movie(movie_id: int):
    query = movies_table.select().where(movies_table.c.id == movie_id)
    movie = await database.fetch_one(query)
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    delete_query = movies_table.delete().where(movies_table.c.id == movie_id)
    await database.execute(delete_query)
    await notify_websockets(movie, "movie_deleted")
    return {"id": movie["id"], "title": movie["title"], "year": movie["year"]}

@app.put("/movies/{movie_id}", response_model=Movie)
async def update_movie(movie_id: int, movie: Movie):
    query = movies_table.select().where(movies_table.c.id == movie_id)
    existing_movie = await database.fetch_one(query)
    if not existing_movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    update_query = movies_table.update().where(movies_table.c.id == movie_id).values(title=movie.title, year=movie.year)
    await database.execute(update_query)
    await notify_websockets({**movie.dict(), "id": movie_id}, "movie_updated")
    return { "title": movie.title, "year": movie.year,"id": movie_id}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    websocket_connections.append(websocket)
    try:
        while True:
            data = await websocket.receive_text()
    except:
        websocket_connections.remove(websocket)

async def notify_websockets(message: dict, message_type: str):
    for connection in websocket_connections:
        await connection.send_json({"type": message_type, "data": message})
