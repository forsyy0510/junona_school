
from app import create_app
from database import db
from models.models import User

app = create_app()

with app.app_context():
    # Check if admin exists
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        print("Creating admin user...")
        admin = User(username='admin', is_admin=True)
        admin.set_password('admin1234')
        db.session.add(admin)
    else:
        print("Updating admin user password...")
        admin.set_password('admin1234')
        admin.is_admin = True
    
    db.session.commit()
    print("Admin user ready: admin / admin1234")
