from flask import send_from_directory

def register_metadata(app):
    @app.route("/manifest.json")
    def manifest():
        return send_from_directory("static", "manifest.json")
    


    
