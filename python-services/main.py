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
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("title", sqlalchemy.String(length=255)),
    sqlalchemy.Column("year", sqlalchemy.Integer),
)

engine = create_async_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

app = FastAPI()
websocket_connections = []


class Movie(BaseModel):
    id : int
    title: str
    year: int

class MovieCreate(BaseModel):
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
async def create_movie(movie: MovieCreate):
    query = movies_table.insert().values(title=movie.title, year=movie.year).returning(movies_table.c.id)
    last_record_id = await database.execute(query)
    movie_data = {**movie.dict(), "id": last_record_id}
    await notify_websockets({"type": "movie_created", "data": movie_data})

    return movie_data


@app.delete("/movies/{id}")
async def delete_movie(id: int):
    print(f"Attempting to delete movie with ID: {id}")
    query = movies_table.delete().where(movies_table.c.id == id).returning(movies_table.c.id)
    result = await database.execute(query)
    print('DATA IS ',result)

    
    
    if result:
        print(f"Movie with ID {id} deleted from database")
        await notify_websockets({"type": "movie_deleted", "data": {"id": id}})
        return {"message": "Movie deleted successfully", "id": id}
    else:
        print(f"Movie with ID {id} not found")
        raise HTTPException(status_code=501, detail="Movie not found")
    

@app.put("/movies/{id}", response_model=Movie)
async def update_movie(id: int, movie: MovieCreate):
    query = movies_table.update().where(movies_table.c.id == id).values(title=movie.title, year=movie.year)
    result = await database.execute(query)
    if result:
        updated_movie = {**movie.dict(), "id": id}
        await notify_websockets({"type": "movie_updated", "data": updated_movie})
        return updated_movie
    else:
        raise HTTPException(status_code=404, detail="Movie not found")



@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    websocket_connections.append(websocket)
    try:
        while True:
            data = await websocket.receive_text()
    except:
        websocket_connections.remove(websocket)


async def notify_websockets(message: dict):
    for connection in websocket_connections:
        try:
            await connection.send_json(message)
        except Exception as e:
            print(f"Error sending WebSocket message: {e}")



