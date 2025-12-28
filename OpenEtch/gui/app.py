import pygame
from tkinter.filedialog import askopenfilename
import os

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
                ("Open File", (5, 20), self.open_file, None),
                ("Generate All", (5, 50), self.generate_all, None),
                ("+", (82, 50), self.open_generate_all_settings, None)
            ],

            "config": [],

            "config_constant": [
                ("X", (self.config_panel_width - 12, 4), self.__close_config, None)
            ]
        }


        self.__preview_panel = pygame.Surface((self.w - self.settings_panel_width, self.h))
        self.__settings_panel = self.__render_settings_panel()
        self.__config_panel = None

    def __close_config(self):
        self.__config_panel = None
        self.__buttons["config"] = []
        self.__buttons["config_constant"] = [
                ("X", (self.config_panel_width - 12, 4), self.__close_config, None)
            ]

    def generate_all(self):
        print("Not Implemented!")

    def open_generate_all_settings(self):
        config_panel = self.__render_config_panel()

        self.__buttons["config"] = [
            ("Generator Settings", (5, 5), None, None)
        ]

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
        for i, (text, xy, func, _) in enumerate(buttons):
            rect = self.font.render(text, True, (255, 255, 255))

            pygame.draw.rect(surface, (100, 100, 100), (xy[0] - 2, xy[1] - 2, rect.get_width() + 4, rect.get_height() + 4))
            surface.blit(rect, xy)

            buttons[i] = (text, (xy[0] + click_offset_x, xy[1] + click_offset_y), func, rect)

    def __render_settings_panel(self) -> pygame.Surface:
        surface = pygame.Surface((self.settings_panel_width, self.h))
        surface.fill(self.SETTINGS_BACKGROUND_COLOUR)

        self.__render_buttons(surface, self.__buttons["settings"])

        return surface

    def __render_config_panel(self) -> pygame.Surface:
        surface = pygame.Surface((self.config_panel_width, self.h))
        surface.fill(self.CONFIGS_BACKGROUND_COLOUR)

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
                            for text, (x, y), func, rect in self.__buttons[key]:
                                if not rect:
                                    continue

                                if x < mx < x + rect.get_width() and y < my < y + rect.get_height():
                                    if func:
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

