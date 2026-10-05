"""WSGI entry point.

Run in development:   flask run
Run in production:    gunicorn --workers 2 --bind 127.0.0.1:8000 wsgi:app
"""

from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run()
