from mangum import Mangum
import sys
import os

# Add parent directory to path to import api module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from api import app

# Mangum adapter for AWS Lambda/Netlify Functions
handler = Mangum(app, lifespan="off")
