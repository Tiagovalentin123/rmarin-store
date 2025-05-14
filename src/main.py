import os
import sys
# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bootstrap import Bootstrap5 # Import Bootstrap5

from src.models.models import db, Customer
from src.routes.store import store_bp
from src.routes.auth import auth_bp # Import auth_bp

def create_app():
    app = Flask(__name__, template_folder="static", static_folder="static")
    app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET_KEY", "a_very_secret_key_for_dev_only")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", f"mysql+pymysql://{os.getenv('DB_USERNAME', 'root')}:{os.getenv('DB_PASSWORD', 'password')}@{os.getenv('DB_HOST', 'localhost')}:{os.getenv('DB_PORT', '3306')}/{os.getenv('DB_NAME', 'mydb')}")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    app.config["STRIPE_PUBLIC_KEY"] = os.getenv("STRIPE_PUBLIC_KEY", "pk_test_YOUR_PUBLIC_KEY")
    app.config["STRIPE_SECRET_KEY"] = os.getenv("STRIPE_SECRET_KEY", "sk_test_YOUR_SECRET_KEY")

    # Initialize Bootstrap5 - Ensure this line is correctly indented
    bootstrap = Bootstrap5(app)

    db.init_app(app)

    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message_category = "info"
    login_manager.login_message = "Por favor, faça login para aceder a esta página."

    @login_manager.user_loader
    def load_user(user_id):
        return Customer.query.get(int(user_id))

    app.register_blueprint(store_bp, url_prefix="/")
    app.register_blueprint(auth_bp, url_prefix="/auth") # Register auth_bp

    with app.app_context():
        db.create_all()
        # from src.routes.store import add_dummy_products # Ensure this is called if needed
        # add_dummy_products() # Call it here if you want products on app start and DB is empty

    return app

if __name__ == "__main__":
    app = create_app()
    port = int(os.environ.get("PORT", 5000))
    # For Render, Gunicorn will handle the host and port. 
    # The debug=True should ideally be False for production, but Gunicorn will override this.
    app.run(debug=True, host="0.0.0.0", port=port)
