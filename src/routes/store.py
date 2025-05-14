from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify, current_app
from flask_login import login_required, current_user # Import login_required and current_user
from src.models.models import db, Product, Customer, Order, OrderItem
from datetime import datetime
import os
import stripe

store_bp = Blueprint("store", __name__, template_folder=os.path.join(os.path.dirname(__file__), "..", "static"))

# --- Helper Functions ---

def get_cart_data():
    cart = session.get("cart", {})
    cart_items = []
    total_price = 0
    if cart:
        product_ids = cart.keys()
        products = Product.query.filter(Product.id.in_(product_ids)).all()
        product_map = {str(p.id): p for p in products}
        for product_id, quantity in list(cart.items()):
            product = product_map.get(product_id)
            if product:
                if quantity > product.stock:
                    flash(f"Stock insuficiente para {product.name}. Quantidade ajustada para {product.stock}.", "warning")
                    quantity = product.stock
                    if quantity <= 0:
                        del cart[product_id]
                        session.modified = True
                        continue
                    else:
                        cart[product_id] = quantity
                        session.modified = True

                item_total = product.price * quantity
                cart_items.append({"product": product, "quantity": quantity, "item_total": item_total})
                total_price += item_total
            else:
                del cart[product_id]
                session.modified = True
                flash(f"Produto ID {product_id} já não está disponível e foi removido do carrinho.", "warning")
    return cart_items, total_price, False

# --- Routes ---

@store_bp.route("/config")
def get_config():
    return jsonify(publicKey=current_app.config["STRIPE_PUBLIC_KEY"])

@store_bp.route("/create-payment-intent", methods=["POST"])
@login_required # User must be logged in to create a payment intent
def create_payment():
    cart = session.get("cart", {})
    if not cart:
        return jsonify(error="Carrinho vazio"), 400

    _, total_price, error = get_cart_data()
    cart = session.get("cart", {})
    if not cart:
         return jsonify(error="Carrinho ficou vazio após verificação de stock"), 400
    if error:
         return jsonify(error="Erro ao processar carrinho"), 400
    if total_price is None or total_price <= 0:
        return jsonify(error="Valor total inválido ou carrinho vazio"), 400

    try:
        intent = stripe.PaymentIntent.create(
            amount=int(total_price * 100),
            currency="brl", # Consider making currency configurable
            automatic_payment_methods={"enabled": True},
            customer=current_user.email # Associate payment with customer email if possible/desired
        )
        return jsonify({"clientSecret": intent.client_secret})
    except Exception as e:
        return jsonify(error=str(e)), 403

@store_bp.route("/catalog")
def catalog():
    add_dummy_products()
    products = Product.query.all()
    return render_template("catalog.html", products=products)

@store_bp.route("/about")
def about():
    return render_template("about.html")

@store_bp.route("/cart")
def view_cart():
    cart_items, total_price, error = get_cart_data()
    return render_template("cart.html", cart_items=cart_items, total_price=total_price)

@store_bp.route("/add_to_cart/<int:product_id>", methods=["POST"])
def add_to_cart(product_id):
    cart = session.get("cart", {})
    product = Product.query.get_or_404(product_id)
    quantity = int(request.form.get("quantity", 1))

    if quantity <= 0:
        flash("Quantidade inválida.", "warning")
        return redirect(url_for("store.catalog"))

    if product.stock <= 0:
        flash("Produto esgotado!", "danger")
        return redirect(url_for("store.catalog"))

    cart_product_id = str(product_id)
    current_quantity = cart.get(cart_product_id, 0)

    if current_quantity + quantity > product.stock:
         flash(f"Não é possível adicionar {quantity}. Apenas {product.stock - current_quantity} restam em stock.", "warning")
         quantity_to_add = product.stock - current_quantity
         if quantity_to_add <= 0:
             flash(f"Stock máximo de {product.name} já no carrinho.", "info")
             return redirect(url_for("store.view_cart"))
    else:
        quantity_to_add = quantity

    cart[cart_product_id] = current_quantity + quantity_to_add
    session["cart"] = cart
    session.modified = True
    flash(f"{quantity_to_add} x {product.name} adicionado(s) ao carrinho.", "success")
    return redirect(url_for("store.view_cart"))

@store_bp.route("/remove_from_cart/<int:product_id>", methods=["POST"])
def remove_from_cart(product_id):
    cart = session.get("cart", {})
    cart_product_id = str(product_id)
    if cart_product_id in cart:
        del cart[cart_product_id]
        session["cart"] = cart
        session.modified = True
        flash("Item removido do carrinho.", "success")
    else:
        flash("Item não encontrado no carrinho.", "warning")
    return redirect(url_for("store.view_cart"))

@store_bp.route("/update_cart/<int:product_id>", methods=["POST"])
def update_cart(product_id):
    cart = session.get("cart", {})
    cart_product_id = str(product_id)
    quantity = int(request.form.get("quantity", 0))
    product = Product.query.get_or_404(product_id)

    if quantity <= 0:
        if cart_product_id in cart:
            del cart[cart_product_id]
            flash("Item removido do carrinho.", "success")
    elif quantity > product.stock:
        flash(f"Apenas {product.stock} itens em stock. Quantidade ajustada.", "warning")
        cart[cart_product_id] = product.stock
    else:
        cart[cart_product_id] = quantity
        flash("Carrinho atualizado.", "info")

    session["cart"] = cart
    session.modified = True
    return redirect(url_for("store.view_cart"))


@store_bp.route("/checkout")
@login_required # User must be logged in to checkout
def checkout():
    cart = session.get("cart", {})
    if not cart:
        flash("O seu carrinho está vazio.", "warning")
        return redirect(url_for("store.catalog"))

    cart_items, total_price, error = get_cart_data()
    cart = session.get("cart", {})
    if not cart:
        flash("O seu carrinho ficou vazio devido a problemas de stock.", "warning")
        return redirect(url_for("store.catalog"))
    if not cart_items:
        flash("Erro ao carregar itens do carrinho.", "danger")
        return redirect(url_for("store.catalog"))

    # Pre-fill customer data if available
    customer_data = {
        "name": current_user.name,
        "email": current_user.email,
        "phone": current_user.phone if current_user.phone else "",
        "address": current_user.address if current_user.address else ""
    }
    return render_template("checkout.html", cart_items=cart_items, total_price=total_price, customer_data=customer_data)

@store_bp.route("/place_order", methods=["POST"])
@login_required # User must be logged in to place an order
def place_order():
    cart = session.get("cart", {})
    payment_method = request.form.get("paymentMethod")

    if not cart:
        return jsonify({"success": False, "error": "Carrinho vazio"}), 400

    # Get customer details from form, but associate with current_user
    name = request.form.get("name")
    email = request.form.get("email") # Email should match current_user.email or be validated
    phone = request.form.get("phone")
    address = request.form.get("address")

    if not all([name, email, phone, address]):
        return jsonify({"success": False, "error": "Por favor, preencha todas as informações do cliente e envio."}), 400
    
    if email != current_user.email:
        # This case should ideally not happen if email field is pre-filled and read-only or validated
        return jsonify({"success": False, "error": "Email inválido."}), 400

    try:
        product_ids = cart.keys()
        with db.session.begin_nested():
            products = Product.query.filter(Product.id.in_(product_ids)).with_for_update().all()
            product_map = {str(p.id): p for p in products}

            total_price = 0
            order_items_to_create = []
            stock_error = False
            for product_id, quantity in cart.items():
                product = product_map.get(product_id)
                if not product:
                    stock_error = True; error_msg = f"Produto ID {product_id} não encontrado."; break
                if quantity > product.stock:
                    stock_error = True; error_msg = f"Stock insuficiente para {product.name}. Apenas {product.stock} disponíveis."; break

                item_total = product.price * quantity
                total_price += item_total
                order_items_to_create.append(OrderItem(product_id=product.id, quantity=quantity, price=product.price))

            if stock_error:
                return jsonify({"success": False, "error": error_msg}), 400

            # Update current_user details if they were changed in the form
            current_user.name = name
            current_user.phone = phone
            current_user.address = address
            # db.session.add(current_user) # Not needed if current_user is already in session
            db.session.flush()

            new_order = Order(customer_id=current_user.id, total_amount=total_price, status="Pending Payment", payment_method=payment_method)
            new_order.items.extend(order_items_to_create)
            db.session.add(new_order)
            db.session.flush()
            order_id = new_order.id

        db.session.commit()
        return jsonify({"success": True, "orderId": order_id, "paymentMethod": payment_method})

    except Exception as e:
        db.session.rollback()
        print(f"Error in place_order: {e}")
        return jsonify({"success": False, "error": f"Erro ao criar o pedido: {e}"}), 500

@store_bp.route("/order/update_payment_status/<int:order_id>", methods=["POST"])
@login_required # Ensure only logged-in users can update their orders (though order_id is the primary key here)
def update_payment_status(order_id):
    data = request.get_json()
    payment_intent_id = data.get("paymentIntentId")
    status = data.get("status")

    order = Order.query.filter_by(id=order_id, customer_id=current_user.id).first()
    if not order:
         return jsonify({"success": False, "error": "Pedido não encontrado ou não pertence a este utilizador"}), 404

    if not payment_intent_id or not status:
        return jsonify({"success": False, "error": "Dados inválidos"}), 400

    if order.status != "Pending Payment":
         return jsonify({"success": False, "error": "Estado do pedido inválido"}), 400

    if status == "succeeded":
        try:
            with db.session.begin_nested():
                order.status = "Processing"
                order.payment_intent_id = payment_intent_id

                stock_error = False
                for item in order.items:
                    product = Product.query.with_for_update().get(item.product_id)
                    if product and product.stock >= item.quantity:
                        product.stock -= item.quantity
                    else:
                        stock_error = True
                        error_product_id = item.product_id
                        break
                if stock_error:
                    raise Exception("Erro crítico de stock ao finalizar o pedido.")
            db.session.commit()

            session.pop("cart", None)
            session.modified = True
            flash(f"Pagamento para o pedido #{order_id} recebido com sucesso!", "success")
            return jsonify({"success": True, "redirectUrl": url_for("store.order_confirmation", order_id=order_id)})

        except Exception as e:
            db.session.rollback()
            print(f"Error updating order status/stock for order {order_id}: {e}")
            return jsonify({"success": False, "error": f"Pagamento recebido, mas erro ao atualizar pedido: {e}"}), 500
    else:
        order.status = "Payment Failed"
        db.session.commit()
        return jsonify({"success": False, "error": "Pagamento falhou"})

@store_bp.route("/order_confirmation/<int:order_id>")
@login_required
def order_confirmation(order_id):
    order = Order.query.filter_by(id=order_id, customer_id=current_user.id).first_or_404()
    return render_template("order_confirmation.html", order=order)

# --- Dummy Product Adding Function ---
def add_dummy_products():
    with current_app.app_context():
        if Product.query.count() == 0:
            image_dir = os.path.join(current_app.static_folder, "images")
            os.makedirs(image_dir, exist_ok=True)
            # Create dummy images if they don't exist
            dummy_images = ["bikini_a.jpg", "shorts_b.jpg", "onepiece_c.jpg"]
            for img_name in dummy_images:
                img_path = os.path.join(image_dir, img_name)
                if not os.path.exists(img_path):
                    try:
                        with open(img_path, "w") as f:
                            f.write("dummy image content") # Create a placeholder file
                        print(f"Created dummy image: {img_path}")
                    except Exception as e:
                        print(f"Error creating dummy image {img_path}: {e}")

            products = [
                Product(name="Bikini Set A", description="Comfortable beach bikini", price=49.99, stock=10, image_url="/static/images/bikini_a.jpg"),
                Product(name="Swim Shorts B", description="Stylish swim shorts", price=39.99, stock=15, image_url="/static/images/shorts_b.jpg"),
                Product(name="One-Piece C", description="Elegant one-piece swimsuit", price=59.99, stock=5, image_url="/static/images/onepiece_c.jpg")
            ]
            try:
                db.session.add_all(products)
                db.session.commit()
                print("Dummy products added.")
            except Exception as e:
                db.session.rollback()
                print(f"Error adding dummy products: {e}")

