from flask import Flask, render_template, redirect, url_for, request, flash, session
from models import db, User, Message
from config import Config

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

with app.app_context():
    db.create_all()

def current_user():
    if 'user_id' in session:
        return User.query.get(session['user_id'])
    return None

@app.context_processor
def inject_user():
    return dict(user=current_user())

@app.route('/')
def index():
    user = current_user()
    return render_template('index.html', user=user)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if User.query.filter_by(username=username).first():
            flash('Username already exists.')
            return redirect(url_for('register'))
        user = User(username=username, password_hash=password)
        db.session.add(user)
        db.session.commit()
        flash('Registration successful. Please login.')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.password_hash == password:
            session['user_id'] = user.id
            flash('Logged in successfully.')
            return redirect(url_for('index'))
        flash('Invalid username or password.')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out.')
    return redirect(url_for('index'))

@app.route('/users')
def users():
    user = current_user()
    if not user:
        return redirect(url_for('login'))
    users = User.query.filter(User.id != user.id).all()
    return render_template('users.html', users=users)

@app.route('/messages')
def messages():
    user = current_user()
    if not user:
        return redirect(url_for('login'))
    received = Message.query.filter_by(recipient_id=user.id).order_by(Message.timestamp.desc()).all()
    return render_template('messages.html', messages=received)

@app.route('/send_message/<int:user_id>', methods=['GET', 'POST'])
def send_message(user_id):
    sender = current_user()
    if not sender:
        return redirect(url_for('login'))
    recipient = User.query.get_or_404(user_id)
    if request.method == 'POST':
        body = request.form['body']
        msg = Message(sender_id=sender.id, recipient_id=recipient.id, body=body)
        db.session.add(msg)
        db.session.commit()
        flash('Message sent!')
        return redirect(url_for('users'))
    return render_template('send_message.html', recipient=recipient)

@app.route('/reply_message/<int:message_id>', methods=['GET', 'POST'])
def reply_message(message_id):
    user = current_user()
    if not user:
        return redirect(url_for('login'))
    original_message = Message.query.get_or_404(message_id)
    recipient = User.query.get_or_404(original_message.sender_id)
    if request.method == 'POST':
        body = request.form['body']
        reply = Message(sender_id=user.id, recipient_id=recipient.id, body=body)
        db.session.add(reply)
        db.session.commit()
        flash('Reply sent!')
        return redirect(url_for('conversation', user_id=recipient.id))
    return render_template('reply_message.html', recipient=recipient, original_message=original_message)

@app.route('/conversations')
def conversations():
    user = current_user()
    if not user:
        return redirect(url_for('login'))
    # Get all user IDs you have sent to or received from
    sent_ids = db.session.query(Message.recipient_id).filter_by(sender_id=user.id)
    received_ids = db.session.query(Message.sender_id).filter_by(recipient_id=user.id)
    user_ids = set([uid for (uid,) in sent_ids.union(received_ids).all() if uid != user.id])
    users = User.query.filter(User.id.in_(user_ids)).all()
    return render_template('conversations.html', users=users)

@app.route('/conversation/<int:user_id>', methods=['GET', 'POST'])
def conversation(user_id):
    user = current_user()
    if not user:
        return redirect(url_for('login'))
    other = User.query.get_or_404(user_id)
    # Get all messages between the two users
    messages = Message.query.filter(
        ((Message.sender_id == user.id) & (Message.recipient_id == other.id)) |
        ((Message.sender_id == other.id) & (Message.recipient_id == user.id))
    ).order_by(Message.timestamp.asc()).all()
    if request.method == 'POST':
        body = request.form['body']
        msg = Message(sender_id=user.id, recipient_id=other.id, body=body)
        db.session.add(msg)
        db.session.commit()
        return redirect(url_for('conversation', user_id=other.id))
    return render_template('conversation.html', other=other, messages=messages)

if __name__ == '__main__':
    app.run(debug=True)