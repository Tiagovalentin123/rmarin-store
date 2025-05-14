from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from src.forms import RegistrationForm, LoginForm
from src.models.models import db, Customer

auth_bp = Blueprint("auth", __name__, template_folder="../static") # Adjusted template_folder path

@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("store.catalog"))
    form = RegistrationForm()
    if form.validate_on_submit():
        customer = Customer(name=form.name.data, email=form.email.data)
        customer.set_password(form.password.data)
        db.session.add(customer)
        db.session.commit()
        flash("A sua conta foi criada com sucesso! Pode agora fazer login.", "success")
        return redirect(url_for("auth.login"))
    return render_template("register.html", title="Registar", form=form)

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("store.catalog"))
    form = LoginForm()
    if form.validate_on_submit():
        customer = Customer.query.filter_by(email=form.email.data).first()
        if customer and customer.check_password(form.password.data):
            login_user(customer, remember=form.remember.data)
            next_page = request.args.get("next")
            flash("Login efetuado com sucesso!", "success")
            return redirect(next_page) if next_page else redirect(url_for("store.catalog"))
        else:
            flash("Login falhou. Verifique o email e a senha.", "danger")
    return render_template("login.html", title="Login", form=form)

@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logout efetuado com sucesso.", "info")
    return redirect(url_for("store.catalog"))

