from ..board_vectors import Vectorizer
from ..vector_configs import *


def generate_etching_mask(pcb, output_dir):
    v = Vectorizer(pcb, etching_mask)
    v.save(f"{output_dir}/etching_mask.pdf")


def generate_silk_mask(pcb, output_dir):
    v = Vectorizer(pcb, silk_mask)
    v.save(f"{output_dir}/silkscreen_mask.pdf")
