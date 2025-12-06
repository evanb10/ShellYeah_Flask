from flask import render_template
from app.main import main_bp

@main_bp.route('/')
def serve_index():
    return render_template('index.html')
