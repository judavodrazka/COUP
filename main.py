from App.connector import Connector
from App.gui import GUI

class App:
    def __init__(self):
        conn = Connector()
        gui = GUI(conn)
        gui.run()

if __name__ == "__main__":
    app = App()