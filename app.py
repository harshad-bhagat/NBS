from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date
import os
import urllib.parse

app = Flask(__name__)
app.secret_key = 'nbs-shreya-secret-2025'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///nbs.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ─────────────────────────── MODELS ───────────────────────────

class Booking(db.Model):
    id          = db.Column(db.Integer, primary_key=True)
    first_name  = db.Column(db.String(80), nullable=False)
    last_name   = db.Column(db.String(80))
    phone       = db.Column(db.String(20), nullable=False)
    service     = db.Column(db.String(100), nullable=False)
    date        = db.Column(db.String(20), nullable=False)
    time        = db.Column(db.String(20))
    notes       = db.Column(db.Text)
    status      = db.Column(db.String(20), default='pending')   # pending / confirmed / cancelled
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)

class BlockedDate(db.Model):
    id    = db.Column(db.Integer, primary_key=True)
    date  = db.Column(db.String(20), unique=True, nullable=False)
    note  = db.Column(db.String(200))

class Message(db.Model):
    id          = db.Column(db.Integer, primary_key=True)
    name        = db.Column(db.String(80), nullable=False)
    phone       = db.Column(db.String(20), nullable=False)
    message     = db.Column(db.Text, nullable=False)
    is_read     = db.Column(db.Boolean, default=False)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)

# ─────────────────────────── HELPERS ──────────────────────────

ADMIN_PASSWORD = 'shreya123'   # Change this!
OWNER_PHONE    = '918010543485'

def whatsapp_url(phone, text):
    return f"https://wa.me/{phone}?text={urllib.parse.quote(text)}"

def notify_owner(text):
    """Returns a WhatsApp link to notify Shreya — open in a new tab server-side trick."""
    return whatsapp_url(OWNER_PHONE, text)

def admin_required(fn):
    from functools import wraps
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get('admin'):
            return redirect(url_for('admin_login'))
        return fn(*args, **kwargs)
    return wrapper

# ─────────────────────────── PUBLIC API ───────────────────────

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/book', methods=['POST'])
def api_book():
    data = request.get_json(force=True)
    first  = (data.get('firstName') or '').strip()
    last   = (data.get('lastName')  or '').strip()
    phone  = (data.get('phone')     or '').strip()
    svc    = (data.get('service')   or '').strip()
    dt     = (data.get('date')      or '').strip()
    tm     = (data.get('time')      or '').strip()
    notes  = (data.get('notes')     or '').strip()

    if not first or not phone or not svc or not dt:
        return jsonify({'ok': False, 'error': 'Missing required fields'}), 400

    # Check blocked date
    if BlockedDate.query.filter_by(date=dt).first():
        return jsonify({'ok': False, 'error': 'Sorry, that date is unavailable. Please choose another date.'}), 409

    booking = Booking(
        first_name=first, last_name=last,
        phone=phone, service=svc,
        date=dt, time=tm, notes=notes
    )
    db.session.add(booking)
    db.session.commit()

    # Build WhatsApp notification text for owner
    wa_text = (
        f"💅 *New Booking #{booking.id}*\n\n"
        f"👤 *Name:* {first} {last}\n"
        f"📞 *Phone:* {phone}\n"
        f"💅 *Service:* {svc}\n"
        f"📅 *Date:* {dt}\n"
        f"⏰ *Time:* {tm or 'Flexible'}\n"
        f"📝 *Notes:* {notes or 'None'}\n\n"
        f"_Reply to confirm appointment_"
    )

    return jsonify({'ok': True, 'booking_id': booking.id})

@app.route('/api/contact', methods=['POST'])
def api_contact():
    data  = request.get_json(force=True)
    name  = (data.get('name')    or '').strip()
    phone = (data.get('phone')   or '').strip()
    msg   = (data.get('message') or '').strip()

    if not name or not phone or not msg:
        return jsonify({'ok': False, 'error': 'Missing required fields'}), 400

    m = Message(name=name, phone=phone, message=msg)
    db.session.add(m)
    db.session.commit()

    wa_text = (
        f"💌 *New Message #{m.id}*\n\n"
        f"👤 *Name:* {name}\n"
        f"📞 *Phone:* {phone}\n"
        f"💬 *Message:* {msg}\n\n"
        f"_From Nails by Shreya website_"
    )

    return jsonify({'ok': True})

@app.route('/api/blocked-dates', methods=['GET'])
def api_blocked_dates():
    blocked = BlockedDate.query.all()
    return jsonify({'dates': [b.date for b in blocked]})

# ─────────────────────────── ADMIN ────────────────────────────

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    error = None
    if request.method == 'POST':
        if request.form.get('password') == ADMIN_PASSWORD:
            session['admin'] = True
            return redirect(url_for('admin_dashboard'))
        error = 'Wrong password. Try again.'
    return render_template('admin_login.html', error=error)

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin', None)
    return redirect(url_for('admin_login'))

@app.route('/admin')
@admin_required
def admin_dashboard():
    bookings  = Booking.query.order_by(Booking.created_at.desc()).all()
    messages  = Message.query.order_by(Message.created_at.desc()).all()
    blocked   = BlockedDate.query.order_by(BlockedDate.date).all()
    unread    = Message.query.filter_by(is_read=False).count()
    pending   = Booking.query.filter_by(status='pending').count()
    return render_template('admin.html',
        bookings=bookings, messages=messages,
        blocked=blocked, unread=unread, pending=pending
    )

@app.route('/admin/booking/<int:bid>/status', methods=['POST'])
@admin_required
def update_booking_status(bid):
    booking = Booking.query.get_or_404(bid)
    status  = request.form.get('status')
    if status in ('confirmed', 'cancelled', 'pending'):
        booking.status = status
        db.session.commit()
    return redirect(url_for('admin_dashboard') + '#bookings')

@app.route('/admin/booking/<int:bid>/delete', methods=['POST'])
@admin_required
def delete_booking(bid):
    booking = Booking.query.get_or_404(bid)
    db.session.delete(booking)
    db.session.commit()
    return redirect(url_for('admin_dashboard') + '#bookings')

@app.route('/admin/message/<int:mid>/read', methods=['POST'])
@admin_required
def mark_read(mid):
    msg = Message.query.get_or_404(mid)
    msg.is_read = True
    db.session.commit()
    return redirect(url_for('admin_dashboard') + '#messages')

@app.route('/admin/block-date', methods=['POST'])
@admin_required
def block_date():
    dt   = request.form.get('date', '').strip()
    note = request.form.get('note', '').strip()
    if dt and not BlockedDate.query.filter_by(date=dt).first():
        db.session.add(BlockedDate(date=dt, note=note))
        db.session.commit()
    return redirect(url_for('admin_dashboard') + '#blocked')

@app.route('/admin/unblock-date/<int:did>', methods=['POST'])
@admin_required
def unblock_date(did):
    bd = BlockedDate.query.get_or_404(did)
    db.session.delete(bd)
    db.session.commit()
    return redirect(url_for('admin_dashboard') + '#blocked')

# ──────────────────────────────────────────────────────────────

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
