from flask import Flask, jsonify
import os

app = Flask(__name__)

def is_virtual_environment_active():
    """Checks if a virtual environment is active."""
    return 'VIRTUAL_ENV' in os.environ

@app.route('/api/venv_status')
def venv_status():
    is_active = is_virtual_environment_active()
    return jsonify({'is_active': is_active})

if __name__ == '__main__':
    app.run(debug=True)
