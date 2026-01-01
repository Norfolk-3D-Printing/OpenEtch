import pygame
from tkinter.filedialog import askopenfilename
import json
import os

from . import generator
from ..mygerber import PCB
from ..mygerber.render.renderer import GerberView
from ..board_vectors import Vectorizer

pygame.init()

class App:
    SETTINGS_BACKGROUND_COLOUR = (30, 30, 30)
    CONFIGS_BACKGROUND_COLOUR = (40, 40, 40)

    PCB_GREEN = (0, 45, 4)

    VERSION = "0.1"

    def __init__(self):
        self.w, self.h = 860, 640
        self.running = False

        self.settings_panel_width = 150
        self.config_panel_width = 150

        self.screen = pygame.display.set_mode((self.w, self.h))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont(pygame.font.get_default_font(), 16)

        pygame.display.set_caption(f"OpenEtch v{self.VERSION} by Norfolk 3D Printing")

        self.pcb = None

        self.__buttons = {
            "settings": [
                {"text": "Open File", "pos": (5, 20), "func": self.open_file},
                {"text": "Generate All", "pos": (5, 50), "func": self.generate_all},
                {"text": "+", "pos": (82, 50), "func": self.open_generate_all_settings}
            ],

            "config": [],

            "config_constant": [
                {"text": "X", "pos": (self.config_panel_width - 12, 4), "func": self.__close_config}
            ]
        }

        self.generate_all_config = json.load(open("generator_config.json", "r"))

        self.__preview_panel = pygame.Surface((self.w - self.settings_panel_width, self.h))
        self.__settings_panel = self.__render_settings_panel()
        self.__config_panel = None

    def __close_config(self):
        self.__config_panel = None
        self.__buttons["config"] = []

    def generate_all(self):
        if not self.pcb:
            print("No PCB Loaded!")
            return

        output_dir = f"{self.pcb.path}_output"
        os.makedirs(output_dir, exist_ok=True)

        for task in self.generate_all_config:
            data = self.generate_all_config[task]

            if data["enabled"]:
                print(f"Generating: {task}")
                run_func = data["run_func"]

                if run_func and hasattr(generator, run_func):
                    getattr(generator, run_func)(self.pcb, output_dir)

            else:
                print(f"Skipping: {task}")




    def toggle_generator_setting(self, text):
        enabled = self.generate_all_config[text]["enabled"]
        self.generate_all_config[text]["enabled"] = not enabled

        json.dump(self.generate_all_config, open("generator_config.json", "w"))

        self.open_generate_all_settings()

    def open_generate_all_settings(self):
        config_panel = self.__render_config_panel()

        self.__buttons["config"] = [
            {"text": "Generator Settings", "pos": (5, 5), "func": None}
        ]

        y = 30
        for config_option in self.generate_all_config:
            config_data = self.generate_all_config[config_option]

            self.__buttons["config"].append(
                {"text": config_option, "pos": (30, y), "func": None}
            )

            self.__buttons["config"].append(
                {"text": f"[{'X' if config_data['enabled'] else '  '}]", "pos": (8, y), "func": self.toggle_generator_setting, "args": (config_option,)}
            )

            y += 20

        self.__render_buttons(config_panel, self.__buttons["config"], click_offset_x=self.settings_panel_width)
        self.__config_panel = config_panel

    def open_file(self):
        filepath = askopenfilename(title="Select a gerber")

        if os.path.exists(filepath):
            try:
                self.pcb = PCB(filepath)
                print(f"Loaded PCB From: {filepath}")
            except Exception as e:
                self.pcb = None
                print("Failed to load PCB:", e)

            if self.pcb:
                self.__generate_pcb_preview()

        else:
            print("File not found!")


    def __generate_pcb_preview(self):
        self.__preview_panel.fill((0, 0, 0))

        pcb_w, pcb_h = self.pcb.get_shape()
        offset = (-self.pcb.min_xy[0], -self.pcb.min_xy[1])

        w_scale = self.__preview_panel.get_width() / pcb_w
        h_scale = self.__preview_panel.get_height() / pcb_h

        scale = min(w_scale, h_scale)

        view = GerberView((round(pcb_w * w_scale), round(pcb_h * h_scale)), True, (0, 0, 0), scale, offset)

        view.draw_pcb_from_outline(self.pcb.get_component("Outline"), self.PCB_GREEN)

        for component_name in self.pcb:
            component = self.pcb.get_component(component_name)
            colour = self.pcb.get_component_colour(component_name)

            view.add_layer(component, colour)

        image_string = view.image.tobytes("raw", "RGBA")
        image = pygame.image.fromstring(image_string, view.image.size, "RGBA")
        self.__preview_panel.blit(image, (0, 0))


    def __render_buttons(self, surface, buttons, click_offset_x=0, click_offset_y=0):
        for i, button in enumerate(buttons):
            text = button.get("text")
            xy = button.get("pos")

            rect = self.font.render(text, True, (255, 255, 255))

            pygame.draw.rect(surface, (100, 100, 100), (xy[0] - 2, xy[1] - 2, rect.get_width() + 4, rect.get_height() + 4))
            surface.blit(rect, xy)

            buttons[i]["rect"] = rect
            buttons[i]["pos"] = (xy[0] + click_offset_x, xy[1] + click_offset_y)

    def __render_settings_panel(self) -> pygame.Surface:
        surface = pygame.Surface((self.settings_panel_width, self.h))
        surface.fill(self.SETTINGS_BACKGROUND_COLOUR)

        self.__render_buttons(surface, self.__buttons["settings"])

        return surface

    def __render_config_panel(self) -> pygame.Surface:
        surface = pygame.Surface((self.config_panel_width, self.h))
        surface.fill(self.CONFIGS_BACKGROUND_COLOUR)

        self.__buttons["config_constant"] = [
            {"text": "X", "pos": (self.config_panel_width - 12, 4), "func": self.__close_config}
        ]

        self.__render_buttons(surface, self.__buttons["config_constant"], click_offset_x=self.settings_panel_width)

        return surface


    def start(self):
        self.running = True

        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False

                if event.type == pygame.MOUSEBUTTONDOWN:
                    mx, my = pygame.mouse.get_pos()

                    if mx < self.settings_panel_width or (self.__config_panel and mx < self.config_panel_width + self.settings_panel_width):
                        for key in self.__buttons:
                            for button in self.__buttons[key]:
                                rect = button.get("rect")
                                x, y = button.get("pos")

                                if not rect:
                                    continue


                                if x < mx < x + rect.get_width() and y < my < y + rect.get_height():
                                    func = button.get("func")
                                    args = button.get("args")

                                    if func:
                                        if args:
                                            func(*args)
                                        else:
                                            func()

                    else:  # Clicked on PCB preview
                        pass

            self.screen.fill((0, 0, 0))
            self.screen.blit(self.__settings_panel, (0, 0))
            self.screen.blit(self.__preview_panel, (self.settings_panel_width, 0))

            if self.__config_panel is not None:
                self.screen.blit(self.__config_panel, (self.settings_panel_width, 0))

            pygame.display.flip()
            self.clock.tick(30)

