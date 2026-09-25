from flask import send_from_directory

def register_metadata(app):
    @app.route("/manifest.json")
    def manifest():
        return send_from_directory("static", "manifest.json")
    
    @app.route("/robots.txt")
    def robots():
        return send_from_directory("static", "robots.txt")
    
    @app.route("/sitemap.xml")
    def sitemap():
        return send_from_directory("static", "sitemap.xml")
    
    @app.route("/llms.txt")
    def llms():
        return send_from_directory("static", "llms.txt")

    


    
