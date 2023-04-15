from statistics import mean
from tkinter import Canvas, Tk, Event, NW
from typing import Tuple, Optional, List, TypeVar


class WBSCanvas(Canvas):
    def __init__(self, master):
        super().__init__(master)
        self.create_oval(0, 0, 10, 10, fill="grey")
        self.bind("<Double-1>", self.create_task)
        self.configure(background="azure")

        self.tasks: List[WBSTaskGraphicalHandler] = []
        self.focus_set()

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
            self.coords(task.rect, x * 70, y * 40, x * 70 + 50, y * 40 + 20)
            self.coords(task.title, x * 70, y * 40)

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
        other.parent = self
        self.children.append(other)


class WBSTaskGraphicalHandler(GraphicalId, TreeStructureHandler):
    def __init__(self, canvas: WBSCanvas, x: int, y: int):
        super().__init__()
        self.canvas = canvas
        self.rect = canvas.create_rectangle(
            x, y, x + 50, y + 20, fill="AliceBlue", tags=("rectangle", self.id)
        )
        self.title = canvas.create_text(
            x, y, text=str(self.rect), anchor=NW, tags=("rectangle_text", self.id)
        )

        self.arrow: Optional[int] = None

        self.canvas.tag_bind(self.rect, "<Button1-Motion>", self.arrow_drag)
        self.canvas.tag_bind(self.rect, "<Button1-ButtonRelease>", self.link_rect)

    def arrow_drag(self, event: Event):
        xm, ym = self.canvas.canvas_pos(event)

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
        self.canvas.tag_lower(self.arrow, "rectangle")

        other_rect = self.canvas.find_closest(
            *self.canvas.canvas_pos(event), start=self.arrow
        )[0]
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
        x0, y0, _, _ = self.canvas.coords(self.rect)
        for child in self.children:
            x1, y1, _, _ = self.canvas.coords(child.rect)

            arrow = self.canvas.create_line(
                x0, y0, x1, y1, arrow="last", tags=("arrow",)
            )
            self.canvas.tag_lower(arrow, "rectangle")


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
