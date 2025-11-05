import os
from dotenv import load_dotenv
from leakfinder import create_app


def main():
    load_dotenv()
    app = create_app()
    port = int(os.environ.get('PORT', '5000'))
    debug = os.environ.get('FLASK_DEBUG', '0') == '1'
    app.run(host='0.0.0.0', port=port, debug=debug)


if __name__ == '__main__':
    main()

