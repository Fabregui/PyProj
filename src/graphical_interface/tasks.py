from tkinter import Toplevel, Widget
from tkinter.ttk import Button

from src.datamodel.object_permanence.tasks import Task


def create_task(master: Widget) -> Task:
    input_window = Toplevel()
    button = Button(input_window, text="Done" ,command=input_window.destroy)
    button.pack(anchor="s")

    master.wait_window(input_window)

    return Task("undefined")