from tkinter import (
    Tk,
    Canvas,
    N,
    E,
    S,
    W,
    NW,
    RIGHT,
    BOTTOM,
    LEFT,
    CENTER,
    NO,
    Label,
    PanedWindow, VERTICAL,
)
from tkinter.ttk import Labelframe, Frame, Treeview, Scrollbar, Style, Separator

from src.datamodel.graphics_to_data_interface import ApplicationData


class SplittedGantt(PanedWindow):
    def __init__(self, master=None):
        super().__init__(
            master=master,
            orient="horizontal",
            opaqueresize=False,
            relief="raised",
            sashwidth=3,
            bg="black",
        )

        self.TPanedwindow1_p1 = TaskView(self)
        self.add(self.TPanedwindow1_p1)
        self.TPanedwindow1_p2 = GanttView(self)
        self.add(self.TPanedwindow1_p2)


class GanttView(Labelframe):
    def __init__(self, master=None):
        super().__init__(master=master, text="Gantt")
        self.task_grid = GanttDrawer(self)

        vsb = Scrollbar(self, orient="vertical", command=self.task_grid.yview)
        vsb.pack(side=RIGHT, expand=True, fill="y")

        hsb = Scrollbar(self, orient="horizontal", command=self.task_grid.xview)
        hsb.pack(side=BOTTOM, expand=True, fill="x")

        self.task_grid.pack(side=LEFT, expand=True, fill="both")
        self.task_grid.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.pack(side=LEFT, expand=True, fill="both")


class GanttDrawer(Canvas):
    def __init__(self, master):
        super().__init__(master=master, width=2000, height=2000)

        gdl = GanttDateLine(master)

        self.create_window(0, 0, anchor="nw", window=gdl, width=2000, height=40)


class GanttDateLine(Frame):
    def __init__(self, master):
        super().__init__(master=master)

        for i in range(20):
            label = Label(
                self,
                width=10,
                text=f"something_{i}",
                bg="grey",
                border=True,
                justify=LEFT,
                borderwidth=2,
                relief="raised",
            )
            label.grid(row=0, column=i * 7, columnspan=7, sticky="ew")
            for j in range(7):
                label = Label(
                    self,
                    width=2,
                    text=f"{j}",
                    bg="blue",
                    border=True,
                    justify=LEFT,
                    relief="raised",
                )
                label.grid(row=2, column=i * 7 + j)


class TaskView(Labelframe):
    def __init__(self, master=None):
        super().__init__(master=master, width=250, text="Tasks")
        self.task_grid = TaskGrid(self)

        vsb = Scrollbar(self, orient="vertical", command=self.task_grid.yview)
        vsb.pack(side=RIGHT, expand=True, fill="y", pady=(20,0))

        hsb = Scrollbar(self, orient="horizontal", command=self.task_grid.xview)
        hsb.pack(side=BOTTOM, expand=True, fill="x")

        self.task_grid.pack(side=LEFT, expand=True, fill="both", pady=(20,0))
        self.task_grid.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.pack_propagate(False)


class TaskGrid(Treeview):
    def __init__(self, master=None):
        super().__init__(master=master, columns=["1", "2", "3", "4"], height=2000, selectmode="extended", show="headings")
        style = Style()
        style.theme_use('alt')

        self.column("#0", anchor=CENTER, stretch=NO, width=20)
        self.heading("#0", text="tree")

        self.column("1", anchor=CENTER, stretch=NO, width=30)
        self.heading("1", text="info")
        self.column("2", anchor=CENTER, stretch=NO, width=40)
        self.heading("2", text="name")

        self.column("3", anchor=CENTER, stretch=NO, width=80)
        self.heading("3", text="predecessor")

        self.column("4", anchor=CENTER, stretch=NO, width=80)
        self.heading("4", text="successor")

    def reload(self):
        for tasks in ApplicationData.tasks:
            self.insert(
                "", "end", open=True, values=[tasks.name, tasks.parent, tasks.children]
            )

    def clear(self):
        pass


if __name__ == "__main__":

    class Runner(Tk):
        def __init__(self):
            super().__init__()
            self.geometry("1000x800+200+200")
            self.bind("<Control-w>", lambda e: self.destroy())
            frame = SplittedGantt(self)
            frame.pack(fill="both", expand=True)

    runner = Runner()
    runner.title("Gantt")
    runner.mainloop()
