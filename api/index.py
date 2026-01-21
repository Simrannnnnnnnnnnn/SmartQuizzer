import sys
import os

# Root directory ko path mein add karna taaki backend/ imports chalein
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import app

# Vercel requirements

# Ye line Vercel ko batati hai ki templates kahan hain
app.template_folder = os.path.join('..', 'frontend', 'templates')
app.static_folder = os.path.join('..', 'frontend', 'static')

# Vercel ko 'app' object dena
application = app

