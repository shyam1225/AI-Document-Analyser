from flask import Flask

from dotenv import load_dotenv

from routes import register_routes


load_dotenv()


app = Flask(__name__)


# Shared application state
state = {

    "text": "",

    "chunks": [],

    "index": None,

    "chat_history": []
}


# Register all routes
register_routes(
    app,
    state
)


if __name__ == "__main__":

    app.run(
        debug=True
    )