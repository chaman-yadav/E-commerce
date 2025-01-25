from flask_login import UserMixin
from datetime import date, datetime

from . import db

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    contact = db.Column(db.String(20), nullable=False)
    address= db.Column(db.String(200), nullable=False)
    city = db.Column(db.String(100), nullable=False)
    dob = db.Column(db.Date, nullable=False)
    reset_token = db.Column(db.String(128), nullable=True)
 
    
    def __repr__(self):
        return f'<User {self.username}>'
    
class RoleApprovalRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    requested_role = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(20), default='pending')  # 'pending', 'approved', 'rejected'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = db.relationship('User', backref='role_requests')

    def __repr__(self):
        return f'<RoleApprovalRequest {self.id} - {self.requested_role}>'


class Product(db.Model):
    __tablename__ = 'product'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(255), nullable=False)
    category = db.Column(db.String(100), nullable=False)
    size = db.Column(db.String(20))  # Ensure this line exists
    colour = db.Column(db.String(20), nullable=True)
    gender = db.Column(db.String(10), nullable=True)  # New field for gender
    quantity = db.Column(db.Integer, nullable=False)
    manufacturer = db.Column(db.String(100), nullable=True)
    country_of_origin = db.Column(db.String(50), nullable=True)
    rating = db.Column(db.Float, nullable=True)
    discount = db.Column(db.Float, default=0.0, nullable=True)
    # Change backref name to avoid conflict
    images = db.relationship('ProductImage', backref='product', lazy=True)
  

    def __repr__(self):
        return f'<Product {self.name}>'
    
class ProductImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    image_url = db.Column(db.String(255), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)

    def __repr__(self):
        return f'<ProductImage {self.image_url}>'


# Cart Table
class Cart(db.Model):
    __tablename__ = "cart"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("product.id", ondelete='CASCADE'), nullable=False)  # Cascade delete
    total_price = db.Column(db.Float, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)

    product = db.relationship("Product", backref=db.backref("cart_items", passive_deletes=True))

    def __repr__(self):
        return f'<Cart {self.id}>'

class Wishlist(db.Model):
    __tablename__ = "wishlist"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"), nullable=True)  # Allow NULL for product_id

    product = db.relationship("Product", backref="wishlist_items")

    def __repr__(self):
        return f'<Wishlist {self.id}>'
# Order Table


class Order(db.Model):
    __tablename__ = "order"
    id = db.Column(db.Integer, primary_key=True)
    order_amount = db.Column(db.Float, nullable=False)
    order_date = db.Column(db.Date, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"), nullable=False)
    status = db.Column(db.String(20), default='Pending')  # New field for order status

    product = db.relationship("Product", backref="order_items")

    def __repr__(self):
        return f'<Order {self.id}>'