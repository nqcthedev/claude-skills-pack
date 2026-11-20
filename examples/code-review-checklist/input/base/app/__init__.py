from flask import Flask

from .db import close_db
from .routes.bookings import bp as bookings_bp


def create_app(config: dict | None = None) -> Flask:
    app = Flask(__name__)
    app.config.from_mapping(DATABASE="booking.sqlite3")
    if config:
        app.config.update(config)
    app.teardown_appcontext(close_db)
    app.register_blueprint(bookings_bp)
    return app
