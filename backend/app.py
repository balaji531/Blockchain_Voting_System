from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, make_response, send_file
from config import Config
from models import db, User, Candidate, Vote, Election
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from passlib.hash import pbkdf2_sha256
from blockchain import BlockchainClient
import csv
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
import os
import io
import tempfile
from web3 import Web3


app = Flask(__name__, template_folder='templates', static_folder='static')
app.config.from_object(Config)

db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

bc = BlockchainClient(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

with app.app_context():
    db.create_all()

@app.route('/')
def home():
    return render_template('home.html')

# -----------------------
# Registration
# -----------------------
@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].strip()
        email = request.form['email'].strip().lower()
        password = request.form['password']
        voter_id = request.form['voter_id'].strip()

        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'danger')
            return redirect(url_for('register'))

        if User.query.filter_by(voter_id=voter_id).first():
            flash('Voter ID already used', 'danger')
            return redirect(url_for('register'))

        acct = bc.w3.eth.account.create()
        blockchain_address = acct.address
        blockchain_private_key = acct.key.hex()

        hashed_password = pbkdf2_sha256.hash(password)

        user = User(
            username=username,
            email=email,
            password_hash=hashed_password,
            voter_id=voter_id,
            role="voter",
            blockchain_address=blockchain_address,
            blockchain_private_key=blockchain_private_key
        )

        db.session.add(user)
        db.session.commit()

        # FUND VOTER (1 ETH)
        try:
            admin_key = app.config['PRIVATE_KEY']
            admin_account = bc.w3.eth.account.from_key(admin_key)
            admin_address = admin_account.address

            fund_tx = {
                'from': admin_address,
                'to': blockchain_address,
                'value': bc.w3.to_wei(1, 'ether'),
                'gas': 21000,
                'gasPrice': bc.w3.eth.gas_price,
                'nonce': bc.w3.eth.get_transaction_count(admin_address),
                'chainId': bc.w3.eth.chain_id
            }

            signed_fund_tx = bc.w3.eth.account.sign_transaction(fund_tx, admin_key)
            tx_hash = bc.w3.eth.send_raw_transaction(signed_fund_tx.raw_transaction)
            print("Funded voter with 1 ETH:", tx_hash.hex())

        except Exception as e:
            print("Funding failed:", str(e))

        # Register voter on contract
        try:
            if bc.contract:
                bc.register_voter(app.config['PRIVATE_KEY'], blockchain_address)
        except Exception as e:
            print("Contract register failed:", str(e))

        flash('Registration successful. Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

# -----------------------
# Login
# -----------------------
@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        email = request.form['email'].strip().lower()
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and pbkdf2_sha256.verify(password, user.password_hash):
            login_user(user)
            return redirect(url_for('vote'))
        flash('Invalid credentials', 'danger')
    return render_template('login.html')

# -----------------------
# Logout
# -----------------------
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

# -----------------------
# Vote page
# -----------------------
@app.route('/vote', methods=['GET','POST'])
@login_required
def vote():
    candidates = Candidate.query.all()
    election = Election.query.filter_by(is_active=True).first()

    if not election:
        return render_template('vote.html', candidates=candidates, election=None)

    if request.method == 'POST':
        try:
            candidate_db_id = int(request.form['candidate'])
        except Exception:
            return jsonify({'success': False, 'error': 'Invalid candidate id'}), 400

        candidate = Candidate.query.get(candidate_db_id)
        if not candidate:
            return jsonify({'success': False, 'error': 'Invalid candidate'}), 400

        # Prevent multiple votes in same election
        if Vote.query.filter_by(user_id=current_user.id, election_id=election.id).first():
            return jsonify({'success': False, 'error': 'You have already voted in this election'}), 400

        candidate_number = candidate.candidate_number

        # The voter should sign their own transaction (we stored private key at registration for demo)
        voter_private_key = getattr(current_user, 'blockchain_private_key', None)
        voter_address = getattr(current_user, 'blockchain_address', None)

        if not voter_private_key or not voter_address:
            return jsonify({'success': False, 'error': 'Voter blockchain account not set on server'}), 500

        try:
            # This will create, sign and broadcast a tx from voter's account to the contract
            tx_hash = bc.cast_vote(voter_private_key, candidate_number, voter_address)
        except Exception as e:
            app.logger.exception("Error casting vote: %s", e)
            return jsonify({'success': False, 'error': str(e)}), 500

        # Save vote record referencing the tx_hash
        vote = Vote(user_id=current_user.id, candidate_id=candidate.id, election_id=election.id, tx_hash=tx_hash)
        db.session.add(vote)
        db.session.commit()
        return jsonify({'success': True, 'tx_hash': tx_hash})

    return render_template('vote.html', candidates=candidates, election=election)

# -----------------------
# API results
# -----------------------
@app.route('/api/results')
def api_results():
    candidates = Candidate.query.all()
    results = []
    for c in candidates:
        count = bc.get_vote_count(c.candidate_number) if bc.contract else 0
        results.append({'id': c.id, 'name': c.name, 'candidate_number': c.candidate_number, 'count': count})
    return jsonify(results)

# -----------------------
# Admin panel
# -----------------------
@app.route('/admin', methods=['GET', 'POST'])
@login_required
def admin_panel():
    if current_user.role != 'admin':
        flash('Unauthorized', 'danger')
        return redirect(url_for('home'))

    election = Election.query.filter_by(is_active=True).first()

    # add candidate
    if request.method == 'POST' and 'name' in request.form:
        name = request.form['name']
        party = request.form.get('party', '')
        age = int(request.form.get('age') or 0)
        qualification = request.form.get('qualification', '')
        description = request.form.get('description', '')
        is_verified = True if request.form.get('is_verified') else False

        last = Candidate.query.order_by(Candidate.candidate_number.desc()).first()
        next_num = last.candidate_number + 1 if last and last.candidate_number else 1

        cand = Candidate(name=name, party=party, age=age, qualification=qualification,
                         description=description, is_verified=is_verified, candidate_number=next_num)
        db.session.add(cand)
        db.session.commit()

        # Optionally sync to blockchain if contract present and admin key present
        try:
            if bc.contract and app.config.get('PRIVATE_KEY'):
                tx = bc.add_candidate(app.config['PRIVATE_KEY'], name)
                flash('Candidate added and contract updated. Tx: ' + tx, 'success')
            else:
                flash('Candidate added (contract not configured).', 'success')
        except Exception as e:
            flash('Candidate added but contract call failed: ' + str(e), 'warning')

        return redirect(url_for('admin_panel'))

    candidates = Candidate.query.all()
    return render_template('admin.html', candidates=candidates, election=election)

# -----------------------
# Edit candidate
# -----------------------
@app.route('/admin/edit/<int:candidate_id>', methods=['GET','POST'])
@login_required
def edit_candidate(candidate_id):
    if current_user.role != 'admin':
        return redirect(url_for('home'))

    cand = Candidate.query.get_or_404(candidate_id)
    if request.method == 'POST':
        cand.name = request.form.get('name')
        cand.party = request.form.get('party')
        cand.age = int(request.form.get('age') or 0)
        cand.qualification = request.form.get('qualification')
        cand.description = request.form.get('description')
        cand.is_verified = True if request.form.get('is_verified') else False
        db.session.commit()
        flash('Candidate updated!', 'success')
        return redirect(url_for('admin_panel'))
    return render_template('edit_candidate.html', candidate=cand)

# -----------------------
# Delete candidate
# -----------------------
@app.route('/admin/delete/<int:candidate_id>', methods=['POST'])
@login_required
def delete_candidate(candidate_id):
    if current_user.role != 'admin':
        return redirect(url_for('home'))
    cand = Candidate.query.get_or_404(candidate_id)
    db.session.delete(cand)
    db.session.commit()
    flash('Candidate removed', 'danger')
    return redirect(url_for('admin_panel'))

# -----------------------
# Start / Stop election
# -----------------------
@app.route('/admin/start', methods=['POST'])
@login_required
def start_election():
    if current_user.role != 'admin':
        return redirect(url_for('home'))
    new = Election(is_active=True)
    db.session.add(new)
    db.session.commit()
    flash('Election started!', 'success')
    return redirect(url_for('admin_panel'))

@app.route('/admin/stop', methods=['POST'])
@login_required
def stop_election():
    if current_user.role != 'admin':
        return redirect(url_for('home'))
    e = Election.query.filter_by(is_active=True).first()
    if e:
        e.is_active = False
        db.session.commit()
    flash('Election stopped!', 'warning')
    return redirect(url_for('admin_panel'))

# -----------------------
# Export CSV
# -----------------------
@app.route('/admin/export-csv')
@login_required
def export_csv():
    if current_user.role != 'admin':
        return redirect(url_for('home'))

    candidates = Candidate.query.all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Candidate No', 'Name', 'Party', 'Vote Count'])
    for c in candidates:
        vote_count = bc.get_vote_count(c.candidate_number) if bc.contract else 0
        writer.writerow([c.candidate_number, c.name, c.party, vote_count])

    response = make_response(output.getvalue())
    response.headers['Content-Disposition'] = 'attachment; filename=results.csv'
    response.mimetype='text/csv'
    return response

# -----------------------
# Export PDF
# -----------------------
@app.route('/admin/export-pdf')
@login_required
def export_pdf():
    if current_user.role != 'admin':
        return redirect(url_for('home'))

    candidates = Candidate.query.all()

    # Use a temp file to avoid writing into the app root
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
    tmp_name = tmp.name
    tmp.close()

    data = [['Candidate No', 'Name', 'Party', 'Vote Count']]
    for c in candidates:
        vote_count = bc.get_vote_count(c.candidate_number) if bc.contract else 0
        data.append([c.candidate_number, c.name, c.party, vote_count])

    pdf = SimpleDocTemplate(tmp_name, pagesize=letter)
    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.gray),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('GRID', (0,0), (-1,-1), 1, colors.black),
        ('ALIGN', (0,0), (-1,-1), 'CENTER')
    ]))
    pdf.build([table])
    return send_file(tmp_name, as_attachment=True, download_name='results.pdf')

# -----------------------
# Make admin (demo route; remove after testing)
# -----------------------
@app.route('/make_admin/<int:user_id>')
@login_required
def make_admin(user_id):
    # keep protected: only admin can promote
    if current_user.role != 'admin':
        return redirect(url_for('home'))
    u = User.query.get(user_id)
    if not u:
        flash('User not found', 'danger')
        return redirect(url_for('admin_panel'))
    u.role = 'admin'
    db.session.commit()
    flash('User promoted to admin', 'success')
    return redirect(url_for('admin_panel'))

if __name__ == '__main__':
    # debug True is fine for local Ganache development
    app.run(host='0.0.0.0', port=5000, debug=True)
