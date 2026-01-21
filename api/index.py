import sys
import os

# Root directory ko path mein add karna taaki backend/ imports chalein
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import app

# Vercel requirements
app.template_folder = '../frontend/templates'
app.static_folder = '../frontend/static'

# Important for Vercel functions
from main import app as application
