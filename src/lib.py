import logging
from json import loads
from typing import cast

from redis import Redis
from redis.exceptions import RedisError
from requests import get

from .config import REDIS_HOST, REDIS_PASSWORD, REDIS_PORT
from .responses import HourModel, ScheduleModel

logging.basicConfig(
    level=logging.INFO, format="[%(asctime)s] [%(name)s/%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


redis = Redis(
    host=REDIS_HOST, port=REDIS_PORT, decode_responses=True, password=REDIS_PASSWORD
)

CACHE_TTL = 60 * 60 * 24


def api_call(params: dict[str, str] | None = None) -> str:
    if params is None:
        params = {}

    response = get("https://apps.marconivr.it/orario/api.php", params=params, timeout=3)
    if response.status_code == 200:
        return response.text

    raise Exception(f"API error: {response.status_code}")


def api(cls: str | None = None, room: str | None = None) -> dict | list:
    if cls and room:
        raise ValueError("Cannot specify both cls and room")

    key = f"class:{cls}" if cls else f"room:{room}" if room else "root"

    try:
        cached = redis.get(key)
    except RedisError:
        logger.exception("Failed to get from cache key=%s", key)
        cached = None

    if cached is None:
        logger.info("Cache miss key=%s", key)
        cached = api_call({"class": cls} if cls else {"room": room} if room else {})
        try:
            redis.set(key, cached, ex=CACHE_TTL)
        except RedisError:
            logger.exception("Failed to set cache key=%s", key)
    else:
        logger.debug("Cache hit key=%s", key)

    return loads(cast(str, cached))


class ScheduleHour:
    def __init__(
        self, room: "Room", cls: "Class", subject: str, teacher: str | None = None
    ):
        self.room: Room = room
        self.cls: Class = cls
        self.subject: str = subject
        self.teacher: str | None = teacher

    def toHourModel(self) -> HourModel:
        return HourModel(
            **{
                "room": self.room.name,
                "class": self.cls.name,
                "subject": self.subject,
                "teacher": self.teacher,
            }
        )

    def __repr__(self):
        return f"<ScheduleHour {self.room} {self.cls} {self.subject} {self.teacher}>"


class ScheduleDay:
    def __init__(self):
        self.hours: dict[int, ScheduleHour] = {}

    def __getitem__(self, hour) -> ScheduleHour:
        return self.hours[hour]

    def __setitem__(self, hour, value):
        self.hours[hour] = value

    def toHourModels(self) -> dict[int, HourModel]:
        return {key: value.toHourModel() for key, value in sorted(self.hours.items())}

    def __repr__(self):
        return f"<ScheduleDay hours={dict(sorted(self.hours.items()))}>"


class Schedule:
    def __init__(self):
        self.days = {day: ScheduleDay() for day in range(1, 6)}

    def __getitem__(self, day) -> ScheduleDay:
        return self.days[day]

    @property
    def monday(self) -> ScheduleDay:
        return self[1]

    @property
    def tuesday(self) -> ScheduleDay:
        return self[2]

    @property
    def wednesday(self) -> ScheduleDay:
        return self[3]

    @property
    def thursday(self) -> ScheduleDay:
        return self[4]

    @property
    def friday(self) -> ScheduleDay:
        return self[5]

    def toScheduleModel(self) -> ScheduleModel:
        return ScheduleModel(
            monday=self.monday.toHourModels(),
            tuesday=self.tuesday.toHourModels(),
            wednesday=self.wednesday.toHourModels(),
            thursday=self.thursday.toHourModels(),
            friday=self.friday.toHourModels(),
        )

    def __repr__(self):
        return f"<Schedule days={self.days}>"


class Class:
    def __init__(self, name: str):
        self.name = name

    @classmethod
    def list(cls) -> list["Class"]:
        return list(map(Class, cast(dict, api()).get("classes", [])))

    @property
    def schedule(self) -> Schedule | None:
        schedule = Schedule()
        res = api(cls=self.name)
        if not res:
            return None
        for hour in res:
            schedule[int(hour["giorno"])][int(hour["ora"])] = ScheduleHour(
                room=Room(hour["aula"]),
                cls=self,
                subject=hour["materia"].strip("- "),
                teacher=hour["prof"].strip() or None,
            )
        return schedule

    def __repr__(self) -> str:
        return f"<Class {self.name}>"


class Room:
    def __init__(self, name: str):
        self.name = name

    @classmethod
    def list(cls) -> list["Room"]:
        return list(map(Room, cast(dict, api()).get("rooms", [])))

    @property
    def schedule(self) -> Schedule | None:
        schedule = Schedule()
        res = api(room=self.name)
        if not res:
            return None
        for hour in res:
            schedule[int(hour["giorno"])][int(hour["ora"])] = ScheduleHour(
                room=self,
                cls=Class(hour["classe"]),
                subject=hour["materia"].strip("- "),
                teacher=hour["prof"].strip() or None,
            )
        return schedule

    def __repr__(self) -> str:
        return f"<Room {self.name}>"
