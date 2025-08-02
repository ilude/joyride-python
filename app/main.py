import os
from datetime import datetime

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Configuration from environment variables
app.config['DEBUG'] = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
app.config['HOST'] = os.getenv('FLASK_HOST', '0.0.0.0')
app.config['PORT'] = int(os.getenv('FLASK_PORT', 5000))
app.config['SERVICE_NAME'] = os.getenv('SERVICE_NAME', 'Flask Status Service')
app.config['SERVICE_VERSION'] = os.getenv('SERVICE_VERSION', '1.0.0')
app.config['ENVIRONMENT'] = os.getenv('ENVIRONMENT', 'development')


@app.route('/')
def status_page():
    """Main status page"""
    return render_template(
        'status.html',
        service_name=app.config['SERVICE_NAME'],
        version=app.config['SERVICE_VERSION'],
        environment=app.config['ENVIRONMENT'],
        current_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC'),
        host=app.config['HOST'],
        port=app.config['PORT']
    )


@app.route('/health')
def health_check():
    """Health check endpoint for monitoring"""
    return jsonify({
        'status': 'healthy',
        'service': app.config['SERVICE_NAME'],
        'version': app.config['SERVICE_VERSION'],
        'environment': app.config['ENVIRONMENT'],
        'timestamp': datetime.now().isoformat()
    })


@app.route('/status')
def detailed_status():
    """Detailed status information in JSON format"""
    return jsonify({
        'service': {
            'name': app.config['SERVICE_NAME'],
            'version': app.config['SERVICE_VERSION'],
            'environment': app.config['ENVIRONMENT'],
            'debug': app.config['DEBUG']
        },
        'system': {
            'timestamp': datetime.now().isoformat(),
            'host': app.config['HOST'],
            'port': app.config['PORT']
        },
        'status': 'running'
    })


if __name__ == '__main__':
    app.run(
        host=app.config['HOST'],
        port=app.config['PORT'],
        debug=app.config['DEBUG']
    )
