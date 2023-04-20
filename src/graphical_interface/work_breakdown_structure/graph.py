import json
import os.path
import tkinter
from tkinter import Canvas, Tk, Event, NW, Label, LEFT, ttk, BOTTOM, X, RIGHT, Y
from typing import Tuple, Optional, List, TypeVar

from src import SRC_ROOT_FOLDER
from src.datamodel.object_permanence.tasks import OnlyOneParent, NoChildOfItself, Task

TASK_DEFAULT_WIDTH = 100
TASK_DEFAULT_WIDTH_STEP = 200
TASK_DEFAULT_HEIGHT = 50
TASK_DEFAULT_HEIGHT_STEP = 100

DEFAULT_FILE_PATH = os.path.join(SRC_ROOT_FOLDER, "temp.json")


class WBSFrame(tkinter.Frame):
    def __init__(self, master=None):
        super().__init__(master)

        canvas = WBSCanvas(self)

        self.vsb = ttk.Scrollbar(master, orient="vertical", command=canvas.yview)
        self.vsb.pack(side=RIGHT, fill=Y)
        self.hsb = ttk.Scrollbar(master, orient="horizontal", command=canvas.xview)
        self.hsb.pack(side=BOTTOM, fill=X)

        canvas.configure(xscrollcommand=self.hsb.set, yscrollcommand=self.vsb.set)
        canvas.pack(side=LEFT, fill="both", expand=True)


class WBSCanvas(Canvas):
    def __init__(self, master=None):
        super().__init__(master)
        self.configure(background="azure")

        self.tasks: List[WBSTaskGraphicalHandler] = []
        self.tree_structure_handler = TreeStructureHandler(self)
        self.focus_set()
        self.bind("<Double-1>", self.create_task)
        self.bind(
            "s",
            lambda e: self.save(DEFAULT_FILE_PATH),
        )
        self.bind(
            "l",
            lambda e: self.load(DEFAULT_FILE_PATH),
        )

    def canvas_pos(self, event: Event) -> Tuple[int, int]:
        return self.canvasx(event.x), self.canvasy(event.y)

    def create_task(self, event: Event) -> None:
        self.tasks.append(WBSTaskGraphicalHandler(self, Task("undefined")))
        self.organize()

    def organize(self):
        self.delete("arrow")

        tree = self.tree_structure_handler.make_tree(
            id_list=[
                task.task_data.technical_id
                for task in self.tasks
                if task.task_data.parent is None
            ]
        )
        tree = [(self.id_to_graphical_handler(task), x, y) for task, x, y in tree]
        for task, x, y in tree:
            y -= 1
            self.coords(
                task.rect, x * TASK_DEFAULT_WIDTH_STEP, y * TASK_DEFAULT_HEIGHT_STEP
            )

        for task, _, _ in tree:
            task.draw_arrow_to_children()

        self.configure(scrollregion=self.bbox("all"))

    def id_to_graphical_handler(self, technical_id: int) -> "WBSTaskGraphicalHandler":
        return next(
            task for task in self.tasks if task.task_data.technical_id == technical_id
        )

    def save(self, path: str):
        save_data = [task.task_data.serialize() for task in self.tasks]

        with open(path, "w") as file:
            json.dump(save_data, file, indent=4)

    def clear(self):
        self.delete("window")
        self.delete("arrow")
        self.tasks = []

    def load(self, path: str):
        self.clear()
        with open(path, "r") as file:
            save_data = json.load(file, indent=4)
        tasks = [Task.deserialize(task_data) for task_data in save_data]
        graphic_tasks = [WBSTaskGraphicalHandler(self, task) for task in tasks]
        self.tasks.extend(graphic_tasks)
        self.organize()


class InvalidLink(Exception):
    pass


class TreeStructureHandler:
    InheritedClasses = TypeVar("InheritedClasses", bound="TreeStructureHandler")

    def __init__(self, canvas: WBSCanvas):
        self.canvas = canvas

    def make_tree(
        self,
        start_id: int = -1,
        x_offset: int = 0,
        y: int = 0,
        id_list: Optional[List[int]] = None,
    ) -> List[Tuple[int, int, int]]:
        if id_list is not None:
            children = id_list
        else:
            children = self.canvas.id_to_graphical_handler(start_id).task_data.children

        if not children:
            return [(start_id, x_offset, y)]
        tree = []

        for child in children:
            child_tree = self.make_tree(child, x_offset, y + 1)
            x_offset = max(x for _, x, _ in child_tree) + 1

            tree.extend(child_tree)

        children_only_tree = [(task, x, y) for task, x, y in tree if task in children]
        x_of_children = [x for task, x, _ in children_only_tree]
        if len(x_of_children) == 1:
            x_pos_parent = max(x_of_children)
        else:
            x_pos_parent = (max(x_of_children) + min(x_of_children)) / 2

        if start_id != -1:
            tree.append((start_id, x_pos_parent, y))

        return tree


class WBSTaskGraphicalHandler:
    def __init__(self, canvas: WBSCanvas, task: Task):
        self.canvas = canvas
        self.task_data = task
        # self.tree_handler = TreeStructureHandler(self.task_data)
        self.graphical_id = f"{self.task_data.name}_{self.task_data.technical_id}"

        text_widget = Label(
            master=self.canvas,
            bg="grey",
            border=True,
            text=self.graphical_id,
            justify=LEFT,
            anchor=NW,
            wraplength=TASK_DEFAULT_WIDTH,
        )
        self.rect = canvas.create_window(
            0,
            0,
            anchor=NW,
            height=TASK_DEFAULT_HEIGHT,
            width=TASK_DEFAULT_WIDTH,
            tags=(
                "window",
                self.graphical_id,
            ),
            window=text_widget,
        )

        self.arrow: Optional[int] = None

        text_widget.bind("<Button1-Motion>", self.arrow_drag)
        text_widget.bind("<Button1-ButtonRelease>", self.link_rect)

    def get_mouse_position_from_rect(self, event: Event) -> Tuple[int, int]:
        x_rect, y_rect = self.canvas.coords(self.rect)
        return event.x + x_rect, event.y + y_rect

    def arrow_drag(self, event: Event):
        xm, ym = self.get_mouse_position_from_rect(event)

        if self.arrow is None:
            self.arrow = self.canvas.create_line(
                xm, ym, xm, ym, arrow="last", tags=("arrow",)
            )
        else:
            x0, y0, _, _ = self.canvas.coords(self.arrow)
            self.canvas.coords(self.arrow, x0, y0, xm, ym)

    def link_rect(self, event: Event):
        if self.arrow is None:
            return
        # remember this line else we could not find the rectangle we want to link to.
        self.canvas.tag_lower(self.arrow, "window")

        xm, ym = self.get_mouse_position_from_rect(event)

        other_rect = self.canvas.find_closest(xm, ym, start=self.arrow)[0]
        try:
            other_task = next(
                task for task in self.canvas.tasks if task.rect == other_rect
            )
            self.tree_link(other_task)
        except (StopIteration, InvalidLink) as e:
            # no rectangle to link to or linking is invalid.
            self.canvas.delete(self.arrow)
        else:
            self.canvas.organize()
        finally:
            self.arrow = None

    def draw_arrow_to_children(self):
        """
        This function takes charge of drawing straight lines with curves from top to bottom.
        The lines look like :

        |
        |_____
             |
             |

        with bends at the two intersection.
        """
        x0, y0 = self.canvas.coords(self.rect)
        x0 += TASK_DEFAULT_WIDTH // 2
        y0 += TASK_DEFAULT_HEIGHT
        for child in self.task_data.children:
            child = self.canvas.id_to_graphical_handler(child)
            x1, y1 = self.canvas.coords(child.rect)
            x1 += TASK_DEFAULT_WIDTH // 2
            curve_factor = 0.5
            curve_dist = min(
                abs((1 - curve_factor) * (y1 - y0) // 2),
                abs(curve_factor * (x1 - x0) // 2),
            )

            start = (x0, y0)
            waypoint1_curve_start = (x0, y0 + curve_dist * (-1 if y1 < y0 else 1))
            waypoint1 = (x0, (y0 + y1) // 2)
            waypoint1_curve_end = (
                x0 + curve_dist * (-1 if x1 < x0 else 1),
                (y0 + y1) // 2,
            )

            waypoint2_curve_start = (
                x1 - curve_dist * (-1 if x1 < x0 else 1),
                (y0 + y1) // 2,
            )
            waypoint2 = (x1, (y0 + y1) // 2)
            waypoint2_curve_end = (
                x1,
                (y0 + y1) // 2 + curve_dist * (-1 if y1 < y0 else 1),
            )
            end = (x1, y1)

            arrow = self.canvas.create_line(
                *start,
                *waypoint1_curve_start,
                *waypoint1,
                *waypoint1_curve_end,
                *waypoint2_curve_start,
                *waypoint2,
                waypoint2_curve_end,
                *end,
                arrow="last",
                tags=("arrow",),
                smooth=True,
            )
            self.canvas.tag_lower(arrow, "window")

    def tree_link(self, other: "WBSTaskGraphicalHandler") -> None:
        try:
            self.task_data.parent_of(other.task_data)
        except (NoChildOfItself, OnlyOneParent):
            raise InvalidLink

    def __repr__(self):
        return self.graphical_id


if __name__ == "__main__":

    class Runner(Tk):
        def __init__(self):
            super().__init__()
            self.geometry("1000x800+200+200")
            self.bind("<Control-w>", lambda e: self.destroy())
            frame = WBSFrame(self)
            frame.pack(fill="both", expand=True)

    runner = Runner()
    runner.title("WBS")
    runner.mainloop()
