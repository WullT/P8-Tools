import json
from dataclasses import dataclass
import pandas as pd

import datetime
from PIL import Image
from io import BytesIO
import base64


@dataclass
class Flower:
    node_id: str
    timestamp: datetime.datetime
    flower_index: int
    class_name: str
    score: float
    width: int
    height: int


@dataclass
class Pollinator:
    node_id: str
    timestamp: datetime.datetime
    pollinator_index: int
    flower_index: int
    class_name: str
    score: float
    crop: str


class Parser:
    def __init__(self, file_path):
        self.flowers = []
        self.pollinators = []
        self.node_id = None
        self.timestamp = None
        with open(file_path) as f:
            self.data = json.load(f)
        self.parse()

    def parse(self):
        metadata = self.data.get("metadata")
        self.node_id = metadata.get("node_id")
        self.timestamp = datetime.datetime.fromisoformat(
            metadata.get("capture_timestamp")
        )
        detections = self.data.get("detections")
        for fl in detections.get("flowers"):
            self.flowers.append(
                Flower(
                    self.node_id,
                    self.timestamp,
                    fl.get("index"),
                    fl.get("class_name"),
                    fl.get("score"),
                    fl.get("size")[0],
                    fl.get("size")[1],
                )
            )
        for pl in detections.get("pollinators"):
            self.pollinators.append(
                Pollinator(
                    self.node_id,
                    self.timestamp,
                    pl.get("index"),
                    pl.get("flower_index"),
                    pl.get("class_name"),
                    pl.get("score"),
                    pl.get("crop", None),
                )
            )

    def get_flower_df(self):
        df = pd.DataFrame(self.flowers)
        return df

    def get_pollinator_df(self):
        df = pd.DataFrame(self.pollinators)
        return df

    def get_pollinator_crop(self, pollinator_index):
        for polli in self.pollinators:
            if polli.pollinator_index == pollinator_index:
                im = Image.open(BytesIO(base64.b64decode(polli.crop)))
                return im
        return None
