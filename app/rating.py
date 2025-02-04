from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from .models import Product, Rating, OrderDetails
from . import db
from sqlalchemy import func

rating = Blueprint("rating", __name__, url_prefix="/rate")


@rating.route("/<int:order_id>", methods=["GET"])
@login_required
def rate_order(order_id):
    # Fetch the order by ID
    order = db.session.get(OrderDetails, order_id)
    if not order:
        flash("Order not found", "error")
        return redirect(url_for("main.home"))

    # Check if the current user is the owner of the order
    if order.user_id != current_user.id:
        flash("You are not authorized to rate this order", "error")
        return redirect(url_for("main.home"))

    # Fetch the products in the order
    products = order.products

    return render_template("rating.html", products=products, order_id=order_id)


@rating.route("/submit_rating", methods=["POST"])
@login_required
def submit_rating_action():
    data = request.get_json()
    product_id = data.get("product_id")
    rating_value = data.get("rating")
    order_id = data.get("order_id")

    if not product_id or not rating_value or not order_id:
        return jsonify({"error": "Invalid data provided"}), 400

    try:
        rating_value = int(rating_value)
        if rating_value < 1 or rating_value > 5:
            return jsonify({"error": "Rating must be between 1 and 5"}), 400
    except ValueError:
        return jsonify({"error": "Invalid rating value"}), 400

    # Check if the order exists and belongs to the current user
    order = db.session.get(OrderDetails, order_id)
    if not order or order.user_id != current_user.id:
        return jsonify({"error": "Unauthorized access to order"}), 403

    # Check if the product exists
    product = db.session.get(Product, product_id)
    if not product:
        return jsonify({"error": "Product not found"}), 404

    # Add or update the rating in the database
    existing_rating = db.session.query(Rating).filter_by(Product_ID=product_id, User_ID=current_user.id).first()
    if existing_rating:
        existing_rating.rating = rating_value
    else:
        new_rating = Rating(Product_ID=product_id, User_ID=current_user.id, rating=rating_value)
        db.session.add(new_rating)
    db.session.commit()

    # Calculate the average rating for the product
    product.avg_rating = round(db.session.query(func.avg(Rating.rating)).filter(Rating.Product_ID == product_id).scalar(), 2)
    db.session.commit()

    return jsonify({"message": "Rating submitted successfully"}), 200
