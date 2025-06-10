import os
from codigo.app import app
#os.system("python -m pip install --upgrade pip")
#os.system("pip install -r requirements.txt")

def start_flask():
    app.run(host='0.0.0.0', port=5000, debug=True)

if __name__ == '__main__':
    start_flask()