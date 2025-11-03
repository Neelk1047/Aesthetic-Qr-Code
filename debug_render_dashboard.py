from app import app
from flask import render_template
import sys, traceback
# When rendering templates outside of an active request (for debugging),
# Flask's url_for needs SERVER_NAME configured so _external or url building works.
with app.test_request_context('/'):
    try:
        print(render_template('dashboard.html', user_qrs=[]))
    except Exception:
        traceback.print_exc()
        sys.exit(1)

print('OK')
