from app import create_app, db

app = create_app()

# Ensure tables exist on the (cloud) database at cold start.
with app.app_context():
    db.create_all()
