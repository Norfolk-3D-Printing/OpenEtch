import math

from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
import shutil
import uuid
import os


from .mygerber import PCB


class Vectorizer:
    canvas_bottom = None
    canvas_top = None

    offset_x = 0.15
    offset_y = 0.15

    def __init__(self, pcb: PCB, config: dict, width_multiplier=1.03, x_scale_adjustment=1.00, y_scale_adjustment=1.00):
        self.internal_name = str(uuid.uuid4())
        self.pcb = pcb

        self.width_multiplier = width_multiplier

        self.offset_x = -self.pcb.min_xy[0]
        self.offset_y = -self.pcb.min_xy[1]

        self.scale_x = x_scale_adjustment
        self.scale_y = y_scale_adjustment


        w, h = self.pcb.get_shape()
        self.shape = w, h
        print(f"[Vectorizer] Creating top canvas: (w: {w}, h: {h})")
        self.canvas_top = canvas.Canvas(f"{self.internal_name}_top.pdf", pagesize=(w * mm, h * mm))
        self.__vectorise(self.canvas_top, config["top"])

        if self.pcb.has_bottom_layer():
            print(f"[Vectorizer] Creating bottom canvas: (w: {w}, h: {h})")
            self.canvas_bottom = canvas.Canvas(f"{self.internal_name}_bottom.pdf", pagesize=(w * mm, h * mm))
            self.__vectorise(self.canvas_bottom, config["bottom"])

    @staticmethod
    def trace_to_polygon(x1, y1, x2, y2, width, arc_steps=12):
        """
        Returns a list of (x, y) points representing a filled trace
        with round end caps.
        """
        dx = x2 - x1
        dy = y2 - y1
        length = math.hypot(dx, dy)

        if length == 0:
            return []

        ux = dx / length
        uy = dy / length

        r = width / 2
        points = []

        start_angle = math.atan2(-uy, -ux) - (math.pi / 2)
        for i in range(arc_steps + 1):
            a = start_angle + math.pi * i / arc_steps
            points.append((
                x1 + math.cos(a) * r,
                y1 + math.sin(a) * r
            ))

        end_angle = math.atan2(uy, ux) - (math.pi / 2)
        for i in range(arc_steps + 1):
            a = end_angle + math.pi * i / arc_steps
            points.append((
                x2 + math.cos(a) * r,
                y2 + math.sin(a) * r
            ))

        return points

    def __flatten(self, points):
        return [coord for pt in points for coord in pt]

    def __vectorise_layer(self, active_canvas, layer):
        if hasattr(layer, "commands"):
            for command in layer.commands:
                if command[0] == "line":
                    x1, y1, x2, y2, width = command[1], command[2], command[3], command[4], command[5]

                    points = self.trace_to_polygon((x1+self.offset_x) * mm * self.scale_x, (y1+self.offset_y) * mm  * self.scale_y,
                                                   (x2+self.offset_x) * mm * self.scale_x, (y2+self.offset_y) * mm  * self.scale_y,
                                                   (width * self.width_multiplier) * mm)

                    path = active_canvas.beginPath()
                    path.moveTo(points[0][0], points[0][1])
                    for point in points[1:]:
                        path.lineTo(point[0], point[1])
                    path.lineTo(points[0][0], points[0][1])
                    path.close()



                    active_canvas.drawPath(path, stroke=0, fill=1)

                if command[0] == "blit":
                    points = [((x + self.offset_x) * mm * self.scale_x,
                               (y + self.offset_y) * mm * self.scale_y) for x, y in command[1]]

                    path = active_canvas.beginPath()
                    path.moveTo(points[0][0], points[0][1])
                    for point in points[1:]:
                        path.lineTo(point[0], point[1])
                    path.close()


                    active_canvas.drawPath(path, stroke=0, fill=1)

                if command[0] == "hole":
                    x, y, diameter = command[1:]

                    active_canvas.circle((x + self.offset_x)*mm * self.scale_x, (y + self.offset_y)*mm * self.scale_y, (diameter/2)*mm, stroke=0, fill=1)

    def __vectorise(self, active_canvas, components: list[str]):
        for component_name in self.pcb:
            if component_name in components:
                component = self.pcb.get_component(component_name)
                self.__vectorise_layer(active_canvas, component)


    def show(self):
        self.canvas_top.showPage()


    def save(self, path=None):
        print(f"[Vectorizer] Saving...")
        self.canvas_top.save()

        if self.canvas_bottom:
            self.canvas_bottom.save()

        if path:
            root_path = ".".join(path.split(".")[:-1]) if path.split(".")[-1] == "pdf" else path
            shutil.copy(f"{self.internal_name}_top.pdf", f"{root_path}_top.pdf")
            os.remove(f"{self.internal_name}_top.pdf")

            if self.canvas_bottom:
                shutil.copy(f"{self.internal_name}_bottom.pdf", f"{root_path}_bottom.pdf")
                os.remove(f"{self.internal_name}_bottom.pdf")
