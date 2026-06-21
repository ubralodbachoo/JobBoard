from app import db
from app.models import User, Job
from wsgi import app


@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Job': Job}


if __name__ == '__main__':
    app.run(debug=True)
