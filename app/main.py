import os
from datetime import datetime
from flask import Flask, jsonify, render_template_string
from dotenv import load_dotenv

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

# Simple HTML template for status page
STATUS_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>{{ service_name }} - Status</title>
    <style>
        body { 
            font-family: Arial, sans-serif; 
            margin: 40px auto; 
            max-width: 800px; 
            background-color: #f5f5f5;
        }
        .container { 
            background: white; 
            padding: 30px; 
            border-radius: 8px; 
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .status { 
            color: #28a745; 
            font-weight: bold; 
            font-size: 24px;
        }
        .info { 
            margin: 15px 0; 
            padding: 10px; 
            background-color: #f8f9fa; 
            border-radius: 4px;
        }
        .environment { 
            display: inline-block; 
            padding: 4px 8px; 
            border-radius: 4px; 
            font-weight: bold; 
            color: white;
            background-color: {{ env_color }};
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>{{ service_name }}</h1>
        <div class="status">🟢 Service is running</div>
        
        <div class="info">
            <strong>Version:</strong> {{ version }}<br>
            <strong>Environment:</strong> <span class="environment">{{ environment }}</span><br>
            <strong>Current Time:</strong> {{ current_time }}<br>
            <strong>Host:</strong> {{ host }}:{{ port }}
        </div>
        
        <h3>API Endpoints:</h3>
        <ul>
            <li><a href="/health">/health</a> - Health check endpoint</li>
            <li><a href="/status">/status</a> - Detailed status information</li>
        </ul>
    </div>
</body>
</html>
'''

@app.route('/')
def status_page():
    """Main status page"""
    env_colors = {
        'production': '#dc3545',
        'staging': '#fd7e14', 
        'development': '#28a745'
    }
    
    return render_template_string(
        STATUS_TEMPLATE,
        service_name=app.config['SERVICE_NAME'],
        version=app.config['SERVICE_VERSION'],
        environment=app.config['ENVIRONMENT'],
        env_color=env_colors.get(app.config['ENVIRONMENT'], '#6c757d'),
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
