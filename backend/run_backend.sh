#!/bin/bash
export FLASK_APP=app.main
export FLASK_ENV=development
cd "$(dirname "$0")"
python -c "from app.main import create_app; app, socketio = create_app(); socketio.run(app, debug=True, host='0.0.0.0', port=8000)"
