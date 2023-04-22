from tkinter import Toplevel, Widget, Entry, StringVar, END, Frame
from tkinter.ttk import Button
from typing import Tuple, Optional

from src.datamodel.object_permanence.tasks import Task


def create_new_task(master: Widget) -> Optional[Task]:
    input_window = TaskWindow.new_task()
    master.wait_window(input_window)
    return input_window.get_new_task()


def modify_task(master: Widget, task: Task) -> Optional[Task]:
    input_window = TaskWindow.from_task(task)
    master.wait_window(input_window)
    return input_window.modify_task()


class TaskWindow(Toplevel):
    def __init__(self, task: Optional[Task] = None):
        super().__init__()

        self.task = task
        self.is_validated = False
        self.name_var = StringVar(master=self)

    def make_gui(self) -> None:

        if self.task is None:
            name = "undefined"
        else:
            name = self.task.name

        self.grab_set()
        self.name_var.set(name)
        task_title_entry = Entry(self, justify="left", textvariable=self.name_var)
        task_title_entry.pack(anchor="n")
        task_title_entry.focus_set()
        task_title_entry.select_range(0, END)
        button = Button(self, text="Done", command=self.validate)
        button.pack(anchor="s")
        self.bind("<Return>", lambda e: self.validate())

    @classmethod
    def from_task(cls, task: Task) -> "TaskWindow":
        out = cls(task)
        out.make_gui()
        return out

    @classmethod
    def new_task(cls) -> "TaskWindow":
        out = cls()
        out.make_gui()
        return out

    def get_task_values(self) -> Tuple[str]:
        return (self.name_var.get(),)

    def get_new_task(self) -> Optional[Task]:
        if self.is_validated:
            return Task(*self.get_task_values())

    def modify_task(self) -> Optional[Task]:
        if self.is_validated:
            self.task.name = self.name_var.get()
            return self.task

    def validate(self):
        self.is_validated = True
        self.destroy()
