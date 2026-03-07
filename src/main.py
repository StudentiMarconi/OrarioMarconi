from fastapi import FastAPI

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
    return Class(cls).schedule.toScheduleModel()


@app.get("/room/{room}")
def get_room(room: str) -> ScheduleModel:
    return Room(room).schedule.toScheduleModel()
