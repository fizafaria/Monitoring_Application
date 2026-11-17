"""Local entrypoint: python run.py"""

import os

from app import create_app

app = create_app()

if __name__ == "__main__":
    # 0.0.0.0 = reachable on all interfaces (LAN / remote browser).
    # Default port 5020 avoids clashes on shared hosts where :5000 is often taken.
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "5020"))
    app.run(debug=True, host=host, port=port)
