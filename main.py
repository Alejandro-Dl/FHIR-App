# main.py
from database import init_db
from app import App

if __name__ == "__main__":
    init_db()
    app = App()
    app.mainloop()