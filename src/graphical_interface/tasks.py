from tkinter import Toplevel, Widget, Entry, StringVar, END, Frame
from tkinter.ttk import Button
from typing import Tuple, Optional

from src.datamodel.object_permanence.tasks import Task


def create_new_task(master: Widget) -> Optional[Task]:
    input_window = TaskWindow()
    master.wait_window(input_window)
    return input_window.get_new_task()


class TaskWindow(Toplevel):
    def __init__(self, master=None):
        super().__init__(master=master)
        self.focus_set()
        self.name_var = StringVar(master=self, value="undefined")

        task_title_entry = Entry(self, justify="left", textvariable=self.name_var)
        task_title_entry.pack(anchor="n")
        task_title_entry.focus_set()
        task_title_entry.select_range(0, END)

        button = Button(self, text="Done", command=self.validate)
        button.pack(anchor="s")

        self.grab_set()
        self.bind("<Return>", lambda e: self.validate())

        self.is_validated = False

    def get_task_values(self) -> Tuple[str]:
        return (self.name_var.get(),)

    def get_new_task(self) -> Optional[Task]:
        if self.is_validated:
            return Task(*self.get_task_values())

    def validate(self):
        self.is_validated = True
        self.destroy()
