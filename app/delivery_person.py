from flask import request, jsonify, render_template, Blueprint, url_for
from flask_mail import Message
from . import db, bcrypt, mail
from .models import OrderDetails, User
from .utils import restrict_to_deliveryPerson
from datetime import datetime
from flask_login import current_user
from sqlalchemy import and_

delivery_person = Blueprint("delivery_person", __name__, url_prefix="/delivery_person")
UNASSIGNED_ORDER_STATUS = "Unassigned"


# Function to create the delivery person account
def create_delivery_person_user():
    delivery_person = db.session.query(User).filter_by(email="delivery@gmail.com").first()
    if not delivery_person:
        hashed_password = bcrypt.generate_password_hash("delivery123").decode("utf-8")
        new_delivery_person = User(
            username="delivery_person",
            email="delivery@gmail.com",
            password=hashed_password,
            role="delivery",
            contact="1234567890",
            address="Street-218, Ahmedabad, Gujarat, India, 38006",
            city="Ahmedabad",
            dob=datetime(1990, 1, 1).date(),
        )
        db.session.add(new_delivery_person)
        db.session.commit()


# Route to render the dashboard
@delivery_person.route("/", methods=["GET"])
@restrict_to_deliveryPerson()
def delivery_person_dashboard():
    order_status_options = [UNASSIGNED_ORDER_STATUS] + OrderDetails.status_options.enums
    return render_template("delivery_dashboard.html", order_status_options=order_status_options)


# Route to get the orders table for delivery person based on order status
@delivery_person.route("/orders_table", methods=["GET"])
@restrict_to_deliveryPerson()
def filtered_orders_table():
    filtered_order_status = request.args.get("order_status")

    is_unassigned_orders = False
    if filtered_order_status == UNASSIGNED_ORDER_STATUS:
        is_unassigned_orders = True
        orders = (
            db.session.query(OrderDetails)
            .filter(
                and_(
                    OrderDetails.user_city == current_user.city,
                    OrderDetails.assigned_delivery_person == None,
                )
            )
            .all()
        )
    elif filtered_order_status in OrderDetails.status_options.enums:
        orders = (
            db.session.query(OrderDetails)
            .filter(
                and_(
                    OrderDetails.user_city == current_user.city,
                    OrderDetails.assigned_delivery_person == current_user,
                    OrderDetails.status == filtered_order_status,
                )
            )
            .all()
        )
    else:
        return jsonify({"error": "Invalid filter for order status"}), 400

    return render_template("delivery_dashboard_orders_table.html", orders=orders, is_unassigned_orders=is_unassigned_orders)


@delivery_person.route("/assign_order", methods=["POST"])
@restrict_to_deliveryPerson()
def assign_order():
    order_id = request.json.get("order_id")
    order = db.session.get(OrderDetails, order_id)
    if order == None:
        return "Order Does Not Exist", 404

    if order.user_city != current_user.city:
        return "You Cannot Take Orders At This Location", 403

    if order.assigned_delivery_person != None:
        return "This order has already been assigned to another delivery person.", 403

    order.assigned_delivery_person_id = current_user.id
    db.session.commit()
    return "The Order Has Successfully Assigned To You", 200


# Route to update the status of an order
@delivery_person.route("/update_status", methods=["POST"])
@restrict_to_deliveryPerson()
def update_status():
    data = request.get_json()
    order_id = data.get("order_id")
    new_status = data.get("status")

    if not order_id or not new_status:
        return jsonify({"error": "Invalid data provided"}), 400

    order = db.session.get(OrderDetails, order_id)

    if not order:
        return jsonify({"error": "Order not found"}), 404

    if new_status not in order.status_options.enums:
        return jsonify({"error": "Invalid Status For Order"}), 400

    if order.assigned_delivery_person != current_user:
        return jsonify({"error", "You Cannot Change the status of this order"}), 400

    if order.delivered_date:
        return jsonify({"error": "Cannot change status of Delivered Order."}), 400

    # Update order status
    order.status = new_status
    db.session.commit()

    # Send email if status is changed to "Delivered"
    if new_status == "Delivered":
        order.delivered_date = datetime.now()
        db.session.commit()
        try:
            send_order_delivered_email(order)
        except Exception as e:
            return jsonify({"error": f"Failed to send email: {str(e)}"}), 500

    return jsonify({"message": f"Status updated successfully to {new_status}"}), 200


# Function to send email to the customer
def send_order_delivered_email(order: "OrderDetails"):
    customer_email = order.user_email  # Assuming the `Order` model has a `user` relationship with an `email` attribute
    ratings_link = url_for("rating.rate_order", order_id=order.id, _external=True)

    msg = Message(
        subject="Your Order Has Been Delivered!",
        recipients=[customer_email],
        html=f"""
        <p>Dear {order.user_name},</p>

        <p>Your order has been successfully delivered.</p>
        <p>Please share your feedback by clicking on the link below:</p>
        <p><a href="{ratings_link}">Rate the product</a></p>

        <p>Thank you for shopping with us!</p>
        <p>Best regards,<br>FusionFits</p>
        """,
    )
    try:
        mail.send(msg)
        print("Email sent successfully.")
    except Exception as e:
        print(f"Failed to send email: {str(e)}")
