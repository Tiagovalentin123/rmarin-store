import os
import sys
# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bootstrap import Bootstrap5

from src.models.models import db, Customer
from src.routes.store import store_bp
from src.routes.auth import auth_bp

def create_app():
    app_instance = Flask(__name__, template_folder="static", static_folder="static")
    app_instance.config["SECRET_KEY"] = os.getenv("FLASK_SECRET_KEY", "a_very_secret_key_for_dev_only")
    # Ensure DATABASE_URL is set in Render's environment variables for PostgreSQL
    # Example: postgresql://user:password@host:port/database
    app_instance.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", f"mysql+pymysql://{os.getenv('DB_USERNAME', 'root')}:{os.getenv('DB_PASSWORD', 'password')}@{os.getenv('DB_HOST', 'localhost')}:{os.getenv('DB_PORT', '3306')}/{os.getenv('DB_NAME', 'mydb')}")
    app_instance.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    app_instance.config["STRIPE_PUBLIC_KEY"] = os.getenv("STRIPE_PUBLIC_KEY", "pk_test_YOUR_PUBLIC_KEY")
    app_instance.config["STRIPE_SECRET_KEY"] = os.getenv("STRIPE_SECRET_KEY", "sk_test_YOUR_SECRET_KEY")

    bootstrap = Bootstrap5(app_instance)
    db.init_app(app_instance)

    login_manager = LoginManager()
    login_manager.init_app(app_instance)
    login_manager.login_view = "auth.login"
    login_manager.login_message_category = "info"
    login_manager.login_message = "Por favor, faça login para aceder a esta página."

    @login_manager.user_loader
    def load_user(user_id):
        return Customer.query.get(int(user_id))

    app_instance.register_blueprint(store_bp, url_prefix="/")
    app_instance.register_blueprint(auth_bp, url_prefix="/auth")

    with app_instance.app_context():
        db.create_all()
        # from src.routes.store import add_dummy_products
        # add_dummy_products()

    return app_instance

# This line makes the 'app' instance available globally for Gunicorn
app = create_app()

if __name__ == "__main__":
    # This part is for local development, Gunicorn will use the 'app' instance above
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host="0.0.0.0", port=port)

