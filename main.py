import OpenEtch
from OpenEtch import Vectorizer

path = r"test_gerber.zip"

pcb = OpenEtch.PCB(path)
vectorizer = Vectorizer(pcb)
vectorizer.save("demo_output")

