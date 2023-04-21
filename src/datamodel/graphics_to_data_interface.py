import json
from typing import List

from src.datamodel.object_permanence.tasks import Task


class PermanenceHandler:
    def save(self):
        pass

    def load(self):
        pass


class ApplicationData:
    tasks: List[Task] = []

    @staticmethod
    def add_task(task: Task) -> None:
        ApplicationData.tasks.append(task)

    @staticmethod
    def save(path: str) -> None:
        save_data = [task.serialize() for task in ApplicationData.tasks]

        with open(path, "w") as file:
            json.dump(save_data, file, indent=4)

    @staticmethod
    def load(path: str) -> None:
        with open(path, "r") as file:
            save_data = json.load(file)
        ApplicationData.tasks = [Task.deserialize(task_data) for task_data in save_data]
