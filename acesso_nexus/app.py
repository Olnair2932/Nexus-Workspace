from flask import Flask, render_template

app = Flask(__name__)

@app.route("/")
def login():
    return render_template("login.html")


@app.route("/painel")
def painel():
    return "<h1>NEXUS — Área do usuário</h1><p>Login confirmado.</p>"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5005, debug=False)
