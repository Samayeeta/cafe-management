from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cafe.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.urandom(24)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
db = SQLAlchemy(app)

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

class MenuItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    available = db.Column(db.Boolean, default=True, nullable=False)
    stock = db.Column(db.Integer, default=0, nullable=False)
    image_path = db.Column(db.String(200)) 

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    menu_item_id = db.Column(db.Integer, db.ForeignKey('menu_item.id'), nullable=False)
    status = db.Column(db.String(50), default="Processing")
    menu_item = db.relationship('MenuItem')

@app.route('/')
def index():
    items = MenuItem.query.all()
    orders = Order.query.all()
    return render_template('index.html', items=items, orders=orders)

@app.route('/add', methods=['POST'])
def add_item():
    name = request.form.get('name')
    price = request.form.get('price')
    category = request.form.get('category')
    stock = request.form.get('stock')
    available = request.form.get('available') == 'on'

    image_file = request.files['image_file']
    if image_file and image_file.filename != '':
        image_filename = image_file.filename
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], image_filename)
        image_file.save(image_path) 
    else:
        flash('Image is required', 'error')
        return redirect(url_for('index'))

    new_item = MenuItem(name=name, price=float(price), category=category, stock=int(stock), available=available, image_path=image_filename)
    db.session.add(new_item)
    db.session.commit()
    flash('Item added successfully!', 'success')
    return redirect(url_for('index'))

@app.route('/order', methods=['POST'])
def place_order():
    item_id = request.form.get('item_id')
    menu_item = MenuItem.query.get_or_404(item_id)

    if menu_item.stock > 0 and menu_item.available:
        menu_item.stock -= 1  
        new_order = Order(menu_item_id=menu_item.id)
        db.session.add(new_order)
        db.session.commit()
        flash(f'Order placed for {menu_item.name}!', 'success')
    else:
        flash(f'{menu_item.name} is out of stock or unavailable.', 'error')
    
    return redirect(url_for('index'))

@app.route('/delete/<int:item_id>')
def delete_item(item_id):
    item_to_delete = MenuItem.query.get_or_404(item_id)
    if item_to_delete.image_path:  
        image_file_path = os.path.join(app.config['UPLOAD_FOLDER'], item_to_delete.image_path)
        if os.path.exists(image_file_path):
            os.remove(image_file_path)
    db.session.delete(item_to_delete)
    db.session.commit()
    flash('Item deleted successfully!', 'success')
    return redirect(url_for('index'))

@app.route('/toggle_availability/<int:item_id>')
def toggle_availability(item_id):
    item = MenuItem.query.get_or_404(item_id)
    item.available = not item.available
    db.session.commit()
    flash('Item availability updated!', 'success')
    return redirect(url_for('index'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)