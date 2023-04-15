import tkinter
from statistics import mean
from tkinter import Canvas, Tk, Event, NW, Text, Label, UNITS, SCROLL, LEFT
from typing import Tuple, Optional, List, TypeVar

TASK_DEFAULT_WIDTH = 100
TASK_DEFAULT_WIDTH_STEP = 200
TASK_DEFAULT_HEIGHT = 50
TASK_DEFAULT_HEIGHT_STEP = 100


class WBSCanvas(Canvas):
    def __init__(self, master):
        super().__init__(master)
        self.configure(background="azure")

        self.tasks: List[WBSTaskGraphicalHandler] = []
        self.focus_set()
        self.bind("<Double-1>", self.create_task)

    def canvas_pos(self, event: Event) -> Tuple[int, int]:
        return self.canvasx(event.x), self.canvasy(event.y)

    def create_task(self, event: Event) -> None:
        x, y = self.canvas_pos(event)
        self.tasks.append(WBSTaskGraphicalHandler(self, x, y))
        self.organize()

    def organize(self):
        metatask = TreeStructureHandler()
        self.delete("arrow")

        metatask.children = [task for task in self.tasks if task.parent is None]

        tree = metatask.make_tree()
        tree = [(task, x, y) for task, x, y in tree if task != metatask]
        for task, x, y in tree:
            y -= 1
            self.coords(
                task.rect, x * TASK_DEFAULT_WIDTH_STEP, y * TASK_DEFAULT_HEIGHT_STEP
            )

        for task, _, _ in tree:
            task.draw_arrow_to_children()


class GraphicalId:
    _id = 0

    def __init__(self):
        super().__init__()
        self.id = f"graph_{GraphicalId._id}"
        GraphicalId._id += 1


class InvalidLink(Exception):
    pass


class TreeStructureHandler:
    InheritedClasses = TypeVar("InheritedClasses", bound="TreeStructureHandler")

    def __init__(self):
        self.parent: Optional[TreeStructureHandler.InheritedClasses] = None
        self.children: List[TreeStructureHandler.InheritedClasses] = []

    def make_tree(
        self, x_offset: int = 0, y: int = 0
    ) -> List[Tuple["InheritedClasses", int, int]]:
        if not self.children:
            return [(self, x_offset, y)]
        tree = []

        for child in self.children:
            child_tree = child.make_tree(x_offset, y + 1)
            x_offset = max(x for _, x, _ in child_tree) + 1

            tree.extend(child_tree)

        tree.append((self, mean(x for _, x, _ in tree), y))

        return tree

    def tree_link(self, other: "TreeStructureHandler") -> None:
        if other.parent is not None:
            raise InvalidLink("Can't have multiple parents :/")
        if self is other:
            raise InvalidLink("Can't link to yourself, dummy.")
        other.parent = self
        self.children.append(other)


class WBSTaskGraphicalHandler(GraphicalId, TreeStructureHandler):
    def __init__(self, canvas: WBSCanvas, x: int, y: int):
        super().__init__()
        self.canvas = canvas

        text_widget = Label(
            master=self.canvas,
            bg="grey",
            border=True,
            text=self.id * 5 + " " + self.id,
            justify=LEFT,
            anchor=NW,
            wraplength=TASK_DEFAULT_WIDTH,
        )
        self.rect = canvas.create_window(
            x,
            y,
            anchor=NW,
            height=TASK_DEFAULT_HEIGHT,
            width=TASK_DEFAULT_WIDTH,
            tags=(
                "window",
                self.id,
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
        for child in self.children:
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

    def __repr__(self):
        return self.id


if __name__ == "__main__":

    class Runner(Tk):
        def __init__(self):
            super().__init__()
            self.geometry("1000x800+200+200")
            self.bind("<Control-w>", lambda e: self.destroy())

            canvas = WBSCanvas(self)
            canvas.pack(fill="both", expand=True)

    runner = Runner()
    runner.title("WBS")
    runner.mainloop()
