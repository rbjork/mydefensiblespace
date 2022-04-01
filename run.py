__author__ = 'dev'
import os
from templates import app
import logging
logging.basicConfig(filename='mdsbugs.log',level=logging.DEBUG)

if __name__ == "__main__":
    app.config.from_object('configurations.DevelopmentConfig')
    logging.info("Launch Flask")
    port = int(os.environ.get("PORT", 5010))
    app.run(host='0.0.0.0', port=port, debug=True)
