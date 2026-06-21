from app import create_app, db
from app.models import User, Job

app = create_app()

with app.app_context():
    db.create_all()


@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Job': Job}


if __name__ == '__main__':
    app.run(debug=True)

