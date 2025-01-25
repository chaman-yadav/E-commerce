from flask_login import login_required, current_user
import random
from flask import Blueprint, render_template, redirect, url_for, flash, request
from .models import Product, Cart, db,Wishlist,Order
from sqlalchemy.orm import joinedload
import sqlalchemy
from datetime import datetime

main = Blueprint('main', __name__)

@main.route('/')
def home():
    products = Product.query.all()
    random_products = products[:126]  # Display a subset of products

    wishlist = [item.product_id for item in Wishlist.query.filter_by(user_id=current_user.id).all()] if current_user.is_authenticated else []
    cart = [item.product_id for item in Cart.query.filter_by(user_id=current_user.id).all()] if current_user.is_authenticated else []

    return render_template('homepage.html', products=random_products, wishlist=wishlist, cart=cart)


@main.route('/product/<int:product_id>')
def product_details(product_id):
    product = Product.query.get_or_404(product_id)
    related_products = get_related_products(product)

    wishlist = [item.product_id for item in Wishlist.query.filter_by(user_id=current_user.id).all()] if current_user.is_authenticated else []
    cat = [item.product_id for item in Cart.query.filter_by(user_id=current_user.id).all()] if current_user.is_authenticated else []

    return render_template('product_details.html', product=product, related_products=related_products, wishlist=wishlist, cat=cat)

def get_related_products(product, limit=5):
    """Finds related products based on category, then manufacturer and name."""
    if not product:
        return []

    # Exclude the current product
    query_criteria = [Product.id != product.id]

    # 1. Prioritize same category
    if product.category:
        query_criteria.append(Product.category == product.category)

    # 2. If same category, filter by manufacturer (only if there are products in the same category)
    #   The subquery counts matching products in the same category
    subquery = db.session.query(db.func.count(Product.id)).filter(
        Product.category == product.category, Product.id != product.id
    ).scalar()
    
    # if subquery > 0 and product.manufacturer:  #Only add manufacturer filter if same category products exist
    #     query_criteria.append(Product.manufacturer == product.manufacturer)

    if subquery > 0 and product.gender:  #Only add gender filter if same category products exist
        query_criteria.append(Product.gender == product.gender)
        
    


    # 3. If no match yet, filter by name similarity (least priority)
    name_parts = product.name.lower().split()  # Use the whole name for similarity
    if not any(isinstance(crit, sqlalchemy.sql.expression.BinaryExpression) for crit in query_criteria): #Check if criteria exist before adding name query
        name_query = " OR ".join([f"name LIKE '%{part}%'" for part in name_parts])
        query_criteria.append(db.text(name_query))


    related_products = (Product.query
                        .filter(*query_criteria)
                        .order_by(db.func.random()) #Add random ordering for diversity
                        .limit(12)
                        .all())

    return related_products

@main.route('/checkout', methods=['GET'])
@login_required
def checkout():
    cart_items = Cart.query.filter_by(user_id=current_user.id).all()
    if not cart_items:
        flash("Your cart is empty!", "danger")
        return redirect(url_for('main.cart'))

    total_price = sum(item.total_price for item in cart_items)
    tax = calculate_tax(total_price)
    grand_total = total_price + tax

    return render_template('checkout.html', cart_items=cart_items, total_price=total_price, tax=tax, grand_total=grand_total)

def calculate_tax(total_price):
    if total_price > 3000:
        return 0
    elif total_price > 2000:
        return 400
    elif total_price > 1000:
        return 200
    elif total_price > 500:
        return 100
    else:
        return 50

@main.route('/place_order', methods=['POST'])
@login_required
def place_order():
    cart_items = Cart.query.filter_by(user_id=current_user.id).all()
    if not cart_items:
        flash("Your cart is empty!", "danger")
        return redirect(url_for('main.cart'))

    total_price = sum(item.total_price for item in cart_items)
    tax = calculate_tax(total_price)
    grand_total = total_price + tax

    # Create a new order for each product in the cart
    for item in cart_items:
        product = Product.query.get(item.product_id)
        if product.quantity < item.quantity:
            flash(f"Insufficient stock for {product.name}!", "danger")
            return redirect(url_for('main.cart'))

        # Reduce the product quantity
        product.quantity -= item.quantity

        # Create a new order
        new_order = Order(
            order_amount=item.total_price,
            order_date=datetime.utcnow().date(),
            user_id=current_user.id,
            product_id=item.product_id,
            status='Pending'
        )
        db.session.add(new_order)

    # Clear the cart
    Cart.query.filter_by(user_id=current_user.id).delete()

    # Commit all changes to the database
    db.session.commit()

    flash("Your order has been placed successfully!", "success")
    return redirect(url_for('main.home'))




















@main.route('/add_to_cart', methods=['POST'])
@login_required
def add_to_cart():
    product_id = request.form.get('product_id')
    product = Product.query.get(product_id)

    if not product:
        flash("Product not found!", "danger")
        return redirect(request.referrer or url_for('main.home'))

    # Check if the product is already in the user's cart
    existing_cart_item = Cart.query.filter_by(user_id=current_user.id, product_id=product.id).first()
    if existing_cart_item:
        # Remove the product from the cart
        db.session.delete(existing_cart_item)
        db.session.commit()
        flash("Product removed from cart!", "success")
    else:
        # Add the product to the cart
        cart_item = Cart(
            user_id=current_user.id,
            product_id=product.id,
            quantity=1,
            total_price=product.price
        )
        db.session.add(cart_item)
        db.session.commit()
        flash("Product added to cart!", "success")

    return redirect(request.referrer or url_for('main.home'))

@main.route('/cart')
@login_required
def cart():
    cart_items = Cart.query.filter_by(user_id=current_user.id).all()
    return render_template('cart.html', cart_items=cart_items)

@main.route('/remove_from_cart', methods=['POST'])
@login_required
def remove_from_cart():
    cart_item_id = request.form.get('cart_item_id')
    cart_item = Cart.query.get(cart_item_id)

    if not cart_item or cart_item.user_id != current_user.id:
        flash("Item not found or unauthorized!", "danger")
        return redirect(url_for('main.cart'))

    db.session.delete(cart_item)
    db.session.commit()
    flash("Item removed from cart!", "success")
    return redirect(url_for('main.cart'))


@main.route('/wishlist', methods=['GET'])
@login_required
def wishlist():
    # Fetch the wishlist items for the logged-in user
    wishlist_items = Wishlist.query.filter_by(user_id=current_user.id).all()
    return render_template('wishlist.html', wishlist_items=wishlist_items)


@main.route('/wishlist', methods=['POST'])
@login_required
def add_to_wishlist():
    product_id = request.form.get('product_id')
    product = Product.query.get(product_id)

    if not product:
        flash("Product not found!", "danger")
        return redirect(url_for('main.home'))

    # Check if the product is already in the user's wishlist
    existing_wishlist_item = Wishlist.query.filter_by(user_id=current_user.id, product_id=product.id).first()
    if not existing_wishlist_item:
        wishlist_item = Wishlist(
            user_id=current_user.id,
            product_id=product.id
        )
        db.session.add(wishlist_item)
        db.session.commit()
        flash(f"'{product.name}' has been added to your wishlist!", "success")
    else:
        flash(f"'{product.name}' is already in your wishlist!", "info")

    return redirect(request.referrer or url_for('main.home'))


@main.route('/remove_from_wishlist', methods=['POST'])
@login_required
def remove_from_wishlist():
    product_id = request.form.get('product_id')
    wishlist_item = Wishlist.query.filter_by(user_id=current_user.id, product_id=product_id).first()

    if not wishlist_item:
        flash("Item not found in wishlist!", "danger")
        return redirect(request.referrer or url_for('main.home'))

    product_name = wishlist_item.product.name
    db.session.delete(wishlist_item)
    db.session.commit()
    flash(f"'{product_name}' has been removed from your wishlist!", "success")

    # Redirect to the referring page, or fallback to home
    referrer = request.referrer
    if referrer and "wishlist" not in referrer:  # Avoid looping back to the wishlist page itself
        return redirect(referrer)
    return redirect(url_for('main.home'))  # Fallback to home page



@main.context_processor
def inject_wishlist():
    """Inject the user's wishlist as a list of product IDs for easier checks in templates."""
    if current_user.is_authenticated:
        wishlist_ids = [item.product_id for item in Wishlist.query.filter_by(user_id=current_user.id).all()]
    else:
        wishlist_ids = []
    return dict(wishlist=wishlist_ids)



@main.route('/search')
def search():
    query = request.args.get('q', '').strip()
    if query:
        search_results = Product.query.filter(
            Product.name.ilike(f'%{query}%') |
            Product.description.ilike(f'%{query}%') |
            Product.category.ilike(f'%{query}%')
        ).all()
    else:
        search_results = []
    
    wishlist = [item.product_id for item in Wishlist.query.filter_by(user_id=current_user.id).all()] if current_user.is_authenticated else []

    return render_template('search_results.html', products=search_results, query=query, wishlist=wishlist)
