"""
Primary Assistant Portfolio Application
Entry point for the Flask application using the factory pattern
"""

import os
from website import create_app

# Create the Flask application using the factory pattern
# Configuration is loaded from config.py based on FLASK_ENV
app = create_app()

if __name__ == '__main__':
    # Use environment variables for configuration
    debug_mode = os.getenv('FLASK_DEBUG', 'False').lower() in ('true', '1', 'yes')
    port = int(os.getenv('FLASK_PORT', '8080'))
    host = os.getenv('FLASK_HOST', '0.0.0.0')

    app.logger.info(f"Starting application on {host}:{port} (debug={debug_mode})")
    app.run(debug=debug_mode, port=port, host=host)
