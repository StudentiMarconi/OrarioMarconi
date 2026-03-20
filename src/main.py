from fastapi import FastAPI, HTTPException

from .lib import Class, Room
from .responses import GetResponse, ScheduleModel

app = FastAPI()


@app.get("/")
def get() -> GetResponse:
    return GetResponse(
        classes=list(map(lambda c: c.name, Class.list())),
        rooms=list(map(lambda r: r.name, Room.list())),
    )


@app.get("/class/{cls}")
def get_class(cls: str) -> ScheduleModel:
    schedule = Class(cls).schedule
    if schedule is None:
        raise HTTPException(404, detail=f"Class {cls} not found")
    return schedule.toScheduleModel()


@app.get("/room/{room}")
def get_room(room: str) -> ScheduleModel:
    schedule = Room(room).schedule
    if schedule is None:
        raise HTTPException(404, detail=f"Room {room} not found")
    return schedule.toScheduleModel()
