from flask import Blueprint, render_template, redirect, url_for, flash, request, session, abort, current_app
from flask_login import login_user, logout_user, login_required,current_user
from .models import User,Product, Wishlist
from . import db, bcrypt, mail
from .forms import ProductForm
from flask_mail import Message
from itsdangerous import URLSafeTimedSerializer
from flask import current_app
from datetime import datetime
from .models import RoleApprovalRequest, Cart
from werkzeug.utils import secure_filename
from app.models import ProductImage
import os  # Make sure to import this module


admin = Blueprint('admin', __name__)

def create_admin_user():
    admin = User.query.filter_by(email='admin@gmail.com').first()
    if not admin:
        hashed_password = bcrypt.generate_password_hash('admin123').decode('utf-8')
        new_admin = User(
            username='admin',
            email='admin@gmail.com',
            password=hashed_password,
            role='admin',
            contact='1234567890',
            address="Admin Address", 
            city='Admin city',
            dob=datetime(1990, 1, 1).date()
        )
        db.session.add(new_admin)
        db.session.commit()

@admin.route('/admin/admin_dashboard')
def admin_dashboard():
    if session.get('role') != 'admin':
        flash('Unauthorized access!', 'danger')
        return redirect(url_for('auth.login'))

    return render_template('admin_dashboard.html', username=session.get('username'))

@admin.route('/admin/view_products')
def view_products():
    if current_user.role != 'admin':
        flash('Unauthorized access!', 'danger')
        return redirect(url_for('auth.login'))

    # Query all products from the database
    products = Product.query.all()
    return render_template('view_products.html', products=products)


@admin.route('/admin/delete_product/<int:product_id>', methods=['POST'])
@login_required
def delete_product(product_id):
    if current_user.role != 'admin':
        flash('Unauthorized access!', 'danger')
        return redirect(url_for('auth.login'))

    product = Product.query.get_or_404(product_id)

    try:
        # Handle related cart items and wishlist items before deleting the product
            # Handle related cart items and wishlist items before deleting the product
        Cart.query.filter_by(product_id=product.id).delete()
    
    # Delete the wishlist items associated with the product
        Wishlist.query.filter_by(product_id=product.id).delete()
        # Delete related product images
        ProductImage.query.filter_by(product_id=product.id).delete()
        # Delete the product
        db.session.delete(product)
        db.session.commit()

        flash(f'Product "{product.name}" has been deleted successfully!', 'success')
        return redirect(url_for('admin.admin_dashboard'))

    except Exception as e:
        db.session.rollback()
        flash(f'An error occurred while deleting the product: {str(e)}', 'danger')
        return redirect(url_for('admin.admin_dashboard'))



@admin.route('/admin/add_product', methods=['GET', 'POST'])
@login_required
def add_product():
    if current_user.role != 'admin':
        flash('Unauthorized access!', 'danger')
        return redirect(url_for('auth.login'))

    form = ProductForm()

    if form.validate_on_submit():
        new_product = Product(
            name=form.name.data,
            price=form.price.data,
            description=form.description.data,
            category=form.category.data,
            size=form.size.data,  # New size field
            colour=form.colour.data,  # New colour field
            gender=form.gender.data,  # New gender field
            quantity=form.quantity.data,
            manufacturer=form.manufacturer.data,
            country_of_origin=form.country_of_origin.data,
            rating=form.rating.data,
            discount=form.discount.data
        )

        try:
            db.session.add(new_product)
            db.session.flush()

            upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')
            if not os.path.exists(upload_folder):
                os.makedirs(upload_folder)

            if form.images.data:
                for image in form.images.data:
                    if hasattr(image, 'filename') and image.filename:
                        filename = secure_filename(image.filename)
                        relative_path = f'uploads/{filename}'
                        image_path = os.path.join(upload_folder, filename)
                        image.save(image_path)

                        new_product_image = ProductImage(
                            image_url=relative_path,
                            product_id=new_product.id
                        )
                        db.session.add(new_product_image)

            db.session.commit()
            flash(f'Product "{new_product.name}" has been added successfully!', 'success')
            return redirect(url_for('admin.admin_dashboard'))

        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred while adding the product: {str(e)}', 'danger')
            return redirect(url_for('admin.add_product'))

    return render_template('add_product.html', form=form)

# @admin.route('/admin/update_product/<int:id>', methods=['GET', 'POST'])
# @login_required
# def update_product(id):
#     if current_user.role != 'admin':
#         flash('Unauthorized access!', 'danger')
#         return redirect(url_for('auth.login'))

#     product = Product.query.get_or_404(id)
#     form = ProductForm(obj=product)

#     if form.validate_on_submit():
#         product.name = form.name.data
#         product.price = form.price.data
#         product.description = form.description.data
#         product.category = form.category.data
#         product.size = form.size.data  # Update size field
#         product.colour = form.colour.data  # Update colour field
#         product.gender = form.gender.data  # Update gender field
#         product.quantity = form.quantity.data
#         product.manufacturer = form.manufacturer.data
#         product.country_of_origin = form.country_of_origin.data
#         product.rating = form.rating.data
#         product.discount = form.discount.data

        # try:
        #     if form.images.data:
        #         for image in product.images:
        #             db.session.delete(image)
        #         for image in form.images.data:
        #             if hasattr(image, 'filename') and image.filename:
        #                 filename = secure_filename(image.filename)
        #                 relative_path = f'uploads/{filename}'
        #                 image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        #                 image.save(image_path)

        #                 new_product_image = ProductImage(
        #                     image_url=relative_path,
        #                     product_id=product.id
        #                 )
        #                 db.session.add(new_product_image)

#             db.session.commit()
#             flash(f'Product "{product.name}" has been updated successfully!', 'success')
#             return redirect(url_for('admin.view_products'))

#         except Exception as e:
#             db.session.rollback()
#             flash(f'An error occurred while updating the product: {str(e)}', 'danger')

#     return render_template('update_product.html', form=form, product=product)



@admin.route('/admin/update_product/<int:id>', methods=['GET', 'POST'])
def update_product(id):
    if current_user.role != 'admin':
        flash('Unauthorized access!', 'danger')
        return redirect(url_for('auth.login'))

    # Fetch the product by its ID
    product = Product.query.get_or_404(id)
    
    form = ProductForm()

    if form.validate_on_submit():  # Check if form is valid on POST
        # Update the product details
        product.name = form.name.data
        product.price = form.price.data
        product.description = form.description.data
        product.size = form.size.data  # Update size field
        product.colour = form.colour.data  # Update colour field
        product.gender = form.gender.data  # Update gender field
        product.category = form.category.data
        product.quantity = form.quantity.data
        product.manufacturer = form.manufacturer.data
        product.country_of_origin = form.country_of_origin.data
        product.rating = form.rating.data
        product.discount = form.discount.data

        try:
            if form.images.data:
                for image in product.images:
                    db.session.delete(image)
                for image in form.images.data:
                    if hasattr(image, 'filename') and image.filename:
                        filename = secure_filename(image.filename)
                        relative_path = f'uploads/{filename}'
                        image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                        image.save(image_path)

                        new_product_image = ProductImage(
                            image_url=relative_path,
                            product_id=product.id
                        )
                        db.session.add(new_product_image)

            # Commit the changes to the database
            db.session.commit()
            flash(f'Product "{product.name}" has been updated successfully!', 'success')
            return redirect(url_for('admin.view_products'))

        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred while updating the product: {str(e)}', 'danger')
            return redirect(url_for('admin.update_product', id=id))  # Redirect to update page on error

    # Pre-populate the form with the current product data
    form.name.data = product.name
    form.price.data = product.price
    form.description.data = product.description
    form.category.data = product.category
    form.quantity.data = product.quantity
    form.size.data = product.size
    form.colour.data = product.colour
    form.gender.data = product.gender
    form.manufacturer.data = product.manufacturer
    form.country_of_origin.data = product.country_of_origin
    form.rating.data = product.rating
    form.discount.data = product.discount

    return render_template('update_product.html', form=form, product=product)
# @admin.route('/admin/add_product', methods=['GET', 'POST'])
# @login_required
# def add_product():
#     if current_user.role != 'admin':
#         flash('Unauthorized access!', 'danger')
#         return redirect(url_for('auth.login'))

#     form = ProductForm()  # Create an instance of the form

#     if form.validate_on_submit():  # Check if form is valid on POST
#         # Create a new product instance
#         new_product = Product(
#             name=form.name.data,
#             price=form.price.data,
#             description=form.description.data,
#             category=form.category.data,
#             quantity=form.quantity.data,
#             manufacturer=form.manufacturer.data,
#             country_of_origin=form.country_of_origin.data,
#             rating=form.rating.data,
#             discount=form.discount.data
#         )

#         try:
#             # Add the product to the session
#             db.session.add(new_product)
#             db.session.flush()  # Flush to get the product ID

#             # Ensure the upload folder exists
#             upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')
#             if not os.path.exists(upload_folder):
#                 os.makedirs(upload_folder)

#             # Handle image uploads
#             if form.images.data:
#                 images = form.images.data
#                 for image in images:
#                     if hasattr(image, 'filename') and image.filename:  # Ensure the file is valid
#                         # Save the image with a relative URL
#                         filename = secure_filename(image.filename)
#                         relative_path = f'uploads/{filename}'  # Only save the relative path
#                         image_path = os.path.join(upload_folder, filename)  # This is the absolute path
#                         image.save(image_path)

#                         # Save the relative path in the database
#                         new_product_image = ProductImage(
#                             image_url=relative_path,  # Save relative path
#                             product_id=new_product.id
#                         )
#                         db.session.add(new_product_image)

#                     else:
#                         flash("One or more files were invalid.", "warning")

#             # Commit all changes to the database
#             db.session.commit()
#             flash(f'Product "{new_product.name}" has been added successfully!', 'success')
#             return redirect(url_for('admin.admin_dashboard'))

#         except Exception as e:
#             db.session.rollback()  # Rollback the transaction in case of an error
#             flash(f'An error occurred while adding the product: {str(e)}', 'danger')
#             return redirect(url_for('admin.add_product'))  # Redirect back to the form on error

#     return render_template('add_product.html', form=form)  # Pass the form to the template




def send_role_approval_email(user, action, requested_role=None):
    """Send an email notification based on the role approval/rejection."""
    msg_subject = ""
    msg_body = ""

    if action == 'approve':
        msg_subject = 'Your Role Approval Request has been Approved'
        msg_body = f'''Hello {user.username},

Your request to change your role to "{requested_role}" has been approved. You can now access the additional features associated with this role.

If you have any questions, feel free to reach out to our support team.

Thank you,
Your Application Team
        '''
    elif action == 'reject':
        msg_subject = 'Your Role Approval Request has been Rejected'
        msg_body = f'''Hello {user.username},

We regret to inform you that your request to change your role to "{requested_role}" has been rejected. If you believe this is a mistake or have questions, please contact support.

Thank you,
Your Application Team
        '''

    msg = Message(msg_subject, sender='chamanyadav38113114@gmail.com', recipients=[user.email])
    msg.body = msg_body

    try:
        mail.send(msg)  # Attempt to send the email
        print(f"Role approval email ({action}) sent successfully to {user.email}!")
    except Exception as e:
        print(f"Error sending role approval email: {e}")


@admin.route('/admin/role_approval_requests', methods=['GET', 'POST'])
def role_approval_requests():
    if session.get('role') != 'admin':
        flash('Unauthorized access!', 'danger')
        return redirect(url_for('auth.login'))

    # Fetch all pending role approval requests
    requests = RoleApprovalRequest.query.filter_by(status='pending').all()

    if request.method == 'POST':
        request_id = request.form.get('request_id')
        action = request.form.get('action')

        if request_id and action:
            role_request = RoleApprovalRequest.query.get(request_id)
            if role_request:
                user = User.query.get(role_request.user_id)

                if action == 'approve':
                    role_request.status = 'approved'
                    user.role = role_request.requested_role
                    db.session.commit()

                    # Send approval email
                    send_role_approval_email(user, action='approve', requested_role=role_request.requested_role)

                    flash(f"User {user.username}'s role has been updated to {role_request.requested_role}.", 'success')

                elif action == 'reject':
                    role_request.status = 'rejected'
                    db.session.commit()

                    # Send rejection email
                    send_role_approval_email(user, action='reject', requested_role=role_request.requested_role)

                    flash(f"Role request for {user.username} has been rejected.", 'info')

    return render_template('role_approval_requests.html', requests=requests)


@admin.route('/admin/user_details', methods=['GET', 'POST'])
def user_details():
    if session.get('role') != 'admin':
        flash('Unauthorized access!', 'danger')
        return redirect(url_for('auth.login'))

    # Filters
    role_filter = request.args.get('role')
    city_filter = request.args.get('city')

    # Query to fetch user details with filters
    query = User.query
    if role_filter:
        query = query.filter_by(role=role_filter)
    if city_filter:
        query = query.filter(User.city.ilike(f"%{city_filter}%"))
    
    users = query.all()

    return render_template('user_details.html', users=users, role_filter=role_filter, city_filter=city_filter)
