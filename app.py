
from flask import Flask, render_template, request, jsonify
from crawler import crawl_website

app = Flask(__name__)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/crawl", methods=["POST"])
def crawl():
    data = request.get_json(silent=True) or {}
    domain = data.get("domain", "").strip()

    if not domain:
        return jsonify({
            "success": False,
            "message": "Domain belum diisi"
        }), 400

    try:
        urls = crawl_website(
            domain,
            max_pages=50,
            max_depth=2
        )

        return jsonify({
            "success": True,
            "total": len(urls),
            "urls": urls
        })

    except ValueError as error:
        return jsonify({
            "success": False,
            "message": str(error)
        }), 400

    except Exception:
        return jsonify({
            "success": False,
            "message": "Terjadi kesalahan saat crawling"
        }), 500


if __name__ == "__main__":
    app.run()
