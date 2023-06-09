import os.path
import tkinter
from tkinter import Canvas, Tk, Event, NW, Label, LEFT, ttk, BOTTOM, X, RIGHT, Y, ALL
from typing import Tuple, Optional, List

from src import SRC_ROOT_FOLDER
from src.datamodel.graphics_to_data_interface import ApplicationData
from src.datamodel.object_permanence.tasks import OnlyOneParent, NoChildOfItself, Task
from src.graphical_interface.tasks import create_new_task, modify_task

TASK_DEFAULT_WIDTH = 100
TASK_DEFAULT_WIDTH_STEP = 200
TASK_DEFAULT_HEIGHT = 50
TASK_DEFAULT_HEIGHT_STEP = 100

DEFAULT_FILE_PATH = os.path.join(SRC_ROOT_FOLDER, "temp.json")


class WBSFrame(tkinter.Frame):
    def __init__(self, master=None):
        super().__init__(master)

        self.canvas = WBSCanvas(self)

        self.vsb = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.vsb.pack(side=RIGHT, fill=Y)
        self.hsb = ttk.Scrollbar(self, orient="horizontal", command=self.canvas.xview)
        self.hsb.pack(side=BOTTOM, fill=X)

        self.canvas.configure(xscrollcommand=self.hsb.set, yscrollcommand=self.vsb.set)
        self.canvas.pack(side=LEFT, fill="both", expand=True)

    def reload(self):
        self.canvas.reload()


class WBSCanvas(Canvas):
    def __init__(self, master=None):
        super().__init__(master)
        self.configure(background="azure")

        self.tasks: List[WBSTaskGraphicalHandler] = []
        self.arrows: List[ArrowHandler] = []
        self.tree_structure_handler = TreeStructureHandler(self)
        self.bind("<Double-1>", self.create_task)
        self.bind("<Map>", self.load_when_visible)
        self.bind("<Unmap>", self.clear_when_no_longer_visible)
        # TODO: add non-bugged zoom

        self.tag_bind("arrow", "<Enter>", self.change_cursor_when_on_arrow)
        self.tag_bind("arrow", "<Leave>", self.change_cursor_when_leave)

    def change_cursor_when_on_arrow(self, event: Event):
        self.config(cursor="X_cursor")

    def change_cursor_when_leave(self, event: Event):
        self.config(cursor="")

    def create_task(self, event: Event) -> None:
        new_task = create_new_task(self)
        if new_task is None:
            return

        ApplicationData.add_task(new_task)
        self.tasks.append(WBSTaskGraphicalHandler(self, new_task))
        self.organize()

    def create_relation(
        self,
        first_task: "WBSTaskGraphicalHandler",
        other_task: "WBSTaskGraphicalHandler",
    ):
        arrow = first_task.real_arrow
        try:
            first_task.task_data.parent_of(other_task.task_data)
        except (NoChildOfItself, OnlyOneParent):
            raise InvalidLink

        arrow.end = other_task
        self.arrows.append(arrow)
        self.organize()

    def delete_relation(self, arrow: "ArrowHandler") -> None:
        arrow.start.task_data.remove_child(arrow.end.task_data)
        self.arrows.remove(arrow)
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

        for arrow in self.arrows:
            arrow.draw_between_start_and_end()

        self.configure(scrollregion=self.bbox("all"))

    def id_to_graphical_handler(self, technical_id: int) -> "WBSTaskGraphicalHandler":
        return next(
            task for task in self.tasks if task.task_data.technical_id == technical_id
        )

    def clear(self):
        self.delete("window")
        self.delete("arrow")
        self.tasks = []

    def load_when_visible(self, event: Event) -> None:
        self.focus_set()
        self.reload()

    def reload(self) -> None:
        self.clear()
        self.tasks = [
            WBSTaskGraphicalHandler(self, task) for task in ApplicationData.tasks
        ]
        ids_to_graphical_handler = {
            task.task_data.technical_id: task for task in self.tasks
        }
        tasks_to_link = [
            (task, ids_to_graphical_handler[child])
            for task in self.tasks
            for child in task.task_data.children
        ]
        self.arrows = [
            ArrowHandler.from_start_and_end(start, end) for start, end in tasks_to_link
        ]
        self.organize()

    def clear_when_no_longer_visible(self, event: Event) -> None:
        self.clear()


class InvalidLink(Exception):
    pass


class TreeStructureHandler:
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
            if start_id == -1:
                return []
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
        self.graphical_id = f"{self.task_data.name}_{self.task_data.technical_id}"

        self.text_widget = Label(
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
            window=self.text_widget,
        )

        self.real_arrow: Optional[ArrowHandler] = None

        self.text_widget.bind("<Button1-Motion>", self.arrow_drag)
        self.text_widget.bind("<Button1-ButtonRelease>", self.link_rect)
        self.text_widget.bind("<Double-1>", self.modify_task)

    def get_mouse_position_from_rect(self, event: Event) -> Tuple[int, int]:
        x_rect, y_rect = self.canvas.coords(self.rect)
        return event.x + x_rect, event.y + y_rect

    def arrow_drag(self, event: Event):
        xm, ym = self.get_mouse_position_from_rect(event)

        if self.real_arrow is None:
            self.real_arrow = ArrowHandler(self.canvas, xm, ym, self)
        else:
            self.real_arrow.update_end(xm, ym)

    def link_rect(self, event: Event):
        if self.real_arrow is None:
            return

        xm, ym = self.get_mouse_position_from_rect(event)
        other_rect = self.canvas.find_closest(
            xm, ym, start=self.real_arrow.graphical_arrow
        )[0]
        try:
            other_task = next(
                task for task in self.canvas.tasks if task.rect == other_rect
            )
            self.canvas.create_relation(self, other_task)
        except (StopIteration, InvalidLink):
            # no rectangle to link to or linking is invalid.
            self.real_arrow.delete()
        finally:
            self.real_arrow = None

    def modify_task(self, event: Event):
        new_task = modify_task(self.canvas, self.task_data)
        if new_task is not None:
            self.text_widget.configure(text=new_task.name)

    def __repr__(self):
        return self.graphical_id


class ArrowHandler:
    def __init__(
        self,
        canvas: WBSCanvas,
        start_x: int,
        start_y: int,
        start_task: WBSTaskGraphicalHandler,
    ):
        self.canvas = canvas
        self.canvas.config(cursor="boat")

        self.x0 = start_x
        self.y0 = start_y

        self.graphical_arrow = self.canvas.create_line(
            start_x, start_y, start_x, start_y, arrow="last", tags=("arrow",)
        )

        # remember this line else we could not find the rectangle we want to link to.
        self.canvas.tag_lower(self.graphical_arrow, "window")

        self.start = start_task
        self.end: Optional[WBSTaskGraphicalHandler] = None

    @classmethod
    def from_start_and_end(
        cls, start: WBSTaskGraphicalHandler, end: WBSTaskGraphicalHandler
    ) -> "ArrowHandler":
        obj = cls(start.canvas, 0, 0, start)
        obj.end = end
        return obj

    def update_end(self, xm: int, ym: int) -> None:
        self.canvas.coords(self.graphical_arrow, self.x0, self.y0, xm, ym)

    def delete(self):
        self.canvas.delete(self.graphical_arrow)
        self.canvas.config(cursor="")
        if self.end is not None:
            self.canvas.delete_relation(self)

    def draw_between_start_and_end(self):
        """
        This function takes charge of drawing straight lines with curves from top to bottom.
        The lines look like :

        |
        |_____
             |
             |

        with bends at the two intersection.
        """
        x0, y0 = self.canvas.coords(self.start.rect)
        x0 += TASK_DEFAULT_WIDTH // 2
        y0 += TASK_DEFAULT_HEIGHT

        x1, y1 = self.canvas.coords(self.end.rect)

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

        self.canvas.delete(self.graphical_arrow)
        self.graphical_arrow = self.canvas.create_line(
            *start,
            *waypoint1_curve_start,
            *waypoint1,
            *waypoint1_curve_end,
            *waypoint2_curve_start,
            *waypoint2,
            *waypoint2_curve_end,
            *end,
            arrow="last",
            tags=("arrow",),
            smooth=True,
        )
        self.canvas.tag_lower(self.graphical_arrow, "window")
        self.canvas.tag_bind(
            self.graphical_arrow, "<Button-1>", lambda e: self.delete()
        )
        self.canvas.config(cursor="")


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
