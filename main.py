from gui import launch_gui
from dotenv import load_dotenv

if __name__ == "__main__":
    load_dotenv()   # ensure env loaded for subprocesses
    launch_gui()