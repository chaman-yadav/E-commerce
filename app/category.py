import sqlite3
from .models import *
from flask import Blueprint, render_template
category = Blueprint('category', __name__)
def product_view_by_gender(gender):
    # Fetch all products
    products_by_gender = db.session.query(Product).filter(Product.gender == gender).all()

    user_id = 1
    # Fetch cart items for the user
    cart = db.session.query(Cart.product_id).filter(Cart.user_id == user_id).all()

    # Fetch wishlist items for the user
    wishlist = db.session.query(Wishlist.product_id).filter(Wishlist.user_id == user_id).all()

    # Convert results to a list of products with image URL
    products = []
    for product in products_by_gender:
        # Fetch the first image URL for the product
        product_image = db.session.query(ProductImage).filter(ProductImage.product_id == product.id).first()

        image_url = product_image.image_url if product_image else None  # Default to None if no image found

        products.append({
            'id': product.id,
            'name': product.name,
            'manufacturer': product.manufacturer,
            'price': product.price,
            'gender': product.gender,
            'rating': product.rating,
            'image_url': image_url
        })

    # Return products, wishlist, and cart
    return products, [row[0] for row in wishlist], [row[0] for row in cart]


def product_view_by_category(category):
    """Fetch the products filtered by category."""
    conn = sqlite3.connect('instance/users.db')
    cursor = conn.cursor()
     # user_id = session.get('user_id', 1)
    user_id=1
    cursor.execute("SELECT id, name, manufacturer, price,  category, rating FROM product where category = ?", (category,))
    products_by_category = cursor.fetchall()
    cart = cursor.execute(
        "SELECT product_id FROM cart WHERE user_id = ?",
        (user_id,)
    ).fetchall()
    wishlist = cursor.execute(
        "SELECT product_id FROM wishlist WHERE user_id = ?",
        (user_id,)
    ).fetchall()
    conn.close()
    return products_by_category,[row[0] for row in wishlist],[row[0] for row in cart]

@category.route('/gender/<gender>')
def product_by_gender(gender):
    """Render the homepage by gender filter."""
    products_by_gender,rests,cat= product_view_by_gender(gender)
    return render_template('gender.html', products_by_gender=products_by_gender,wis=rests,cat=cat)

@category.route('/category/<category>')
def product_by_category(category):
    """Render the homepage by category filter."""
    products_by_category,stt,cat= product_view_by_category(category)
    return render_template('category.html', products_by_category=products_by_category,wis=stt,cat=cat)
