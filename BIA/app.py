# app.py
from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os, re, unicodedata

app = Flask(__name__)
app.secret_key = "troque-esta-secret"  # troque em produção

# Uploads
UPLOAD_FOLDER = os.path.join("static", "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
ALLOWED_EXT = {"png", "jpg", "jpeg", "gif"}
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXT

# =========================
# Modelo (mesmo do projeto)
# =========================
np.random.seed(42)
COLS = ["idade", "sexo", "temperatura", "frequencia_cardiaca",
        "pressao_sistolica", "pressao_diastolica", "saturacao",
        "tosse", "fadiga", "sede_excessiva", "vomitos", "falta_ar"]

dados, alvos = [], []
for _ in range(400):
    idade = np.random.randint(1, 90)
    sexo = np.random.choice([0, 1])
    temp = np.random.normal(36.8, 0.8)
    fc = np.random.randint(60, 120)
    pas = np.random.randint(90, 150)
    pad = np.random.randint(60, 100)
    sat = np.random.randint(85, 100)

    tosse = np.random.choice([0, 1])
    fadiga = np.random.choice([0, 1])
    sede = np.random.choice([0, 1])
    vomitos = np.random.choice([0, 1])
    falta_ar = np.random.choice([0, 1])
    dor_cabeca = np.random.choice([0, 1])

    if sede and idade < 18 and temp > 36.5:
        alvo = "Diabetes Tipo 1"
    elif tosse and falta_ar and sat < 93:
        alvo = "Pneumonia"
    elif falta_ar and sat < 90:
        alvo = "Crise Asmática"
    elif pas < 90 or pad < 60:
        alvo = "Hipotensão"
    elif vomitos and sede:
        alvo = "Desidratação"
    else:
        alvo = "Gripe"

    dados.append([idade, sexo, temp, fc, pas, pad, sat, tosse, fadiga, sede, vomitos, falta_ar])
    alvos.append(alvo)

X = pd.DataFrame(dados, columns=COLS)
y = pd.Series(alvos)
X.columns = X.columns.astype(str)

model = RandomForestClassifier(n_estimators=200, random_state=42)
model.fit(X, y)

# =========================
# Parser de sintomas em texto (do seu app)
# =========================
def _normalize(txt: str) -> str:
    if not txt:
        return ""
    txt = unicodedata.normalize("NFD", txt).encode("ascii", "ignore").decode("ascii")
    return txt.lower()

KW = {
    "tosse":         [r"\btosse(m|s)?\b", r"\btossindo\b", r"\bcof\b"],
    "fadiga":        [r"\bfadiga\b", r"\bcansac[oa]\b", r"\bexaust[a|o]\b", r"\bprostrac?ao\b"],
    "sede_excessiva":[r"\bsede\b", r"\bpolidips?ia\b", r"\bmuita sede\b"],
    "vomitos":       [r"\bvomit(o|os|ou|ando)?\b", r"\benjoo\b", r"\bnauseas?\b"],
    "falta_ar":      [r"\bfalta de ar\b", r"\bdificuldade para? respirar\b", r"\bdispneia?\b", r"\bchiado\b", r"\bsufoc[oa]\b"],
}

def parse_symptoms_text(texto: str) -> dict:
    t = _normalize(texto)
    flags = {k: 0 for k in ["tosse","fadiga","sede_excessiva","vomitos","falta_ar"]}
    for key, patterns in KW.items():
        for pat in patterns:
            if re.search(pat, t):
                flags[key] = 1
                break
    return flags

# =========================
# "Banco" de usuários (memória)
# =========================
# Estrutura: users[username] = { "name": display_name, "pass": hash, "photo": url_relativa }
users = {}

# =========================
# Rotas
# =========================
def current_user():
    uname = session.get("user")
    return users.get(uname) if uname in users else None

@app.get("/")
def home():
    # exige login
    if "user" not in session:
        return redirect(url_for("login"))
    user = current_user()
    return render_template("index.html", user=user)

@app.get("/login")
def login():
    if "user" in session:
        return redirect(url_for("home"))
    return render_template("login.html")

@app.post("/login")
def login_post():
    username = (request.form.get("username") or "").strip()
    password = request.form.get("password") or ""
    if username in users and check_password_hash(users[username]["pass"], password):
        session["user"] = username
        return redirect(url_for("home"))
    # credenciais inválidas
    return render_template("login.html", error="Usuário ou senha inválidos.", last_user=username), 401

@app.get("/register")
def register():
    if "user" in session:
        return redirect(url_for("home"))
    return render_template("register.html")

@app.post("/register")
def register_post():
    username = (request.form.get("username") or "").strip()
    display_name = (request.form.get("display_name") or "").strip()
    password = request.form.get("password") or ""
    confirm = request.form.get("confirm") or ""
    photo = request.files.get("photo")

    # validações básicas
    if not username or not password or not display_name:
        return render_template("register.html", error="Preencha usuário, nome e senha."), 400
    if password != confirm:
        return render_template("register.html", error="As senhas não conferem."), 400
    if username in users:
        return render_template("register.html", error="Usuário já existe."), 400

    # salva foto se enviada
    photo_url = None
    if photo and photo.filename and allowed_file(photo.filename):
        fname = secure_filename(photo.filename)
        # evita colisão de nome adicionando username
        root, ext = os.path.splitext(fname)
        fname = f"{username}{ext.lower()}"
        save_path = os.path.join(app.config["UPLOAD_FOLDER"], fname)
        photo.save(save_path)
        photo_url = f"/static/uploads/{fname}"

    # cria usuário
    users[username] = {
        "name": display_name,
        "pass": generate_password_hash(password),
        "photo": photo_url
    }
    session["user"] = username
    return redirect(url_for("home"))

@app.get("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.post("/api/predict")
def predict():
    try:
        if "user" not in session:
            return jsonify({"ok": False, "error": "Não autenticado."}), 401

        data = request.get_json(force=True)
        idade = int(data["idade"])
        sexo = 1 if data["sexo"] == "Masculino" else 0
        temp = float(data["temperatura"])
        fc = int(data["frequencia_cardiaca"])
        pas = int(data["pressao_sistolica"])
        pad = int(data["pressao_diastolica"])
        sat = int(data["saturacao"])


        # checkboxes
        tosse = int(data.get("tosse", 0))
        fadiga = int(data.get("fadiga", 0))
        sede = int(data.get("sede_excessiva", 0))
        vomitos = int(data.get("vomitos", 0))
        falta_ar = int(data.get("falta_ar", 0))

        # texto livre -> OR
        sint_texto = data.get("sintomas_texto", "") or ""
        if sint_texto.strip():
            flags = parse_symptoms_text(sint_texto)
            tosse     = 1 if (tosse or flags["tosse"]) else 0
            fadiga    = 1 if (fadiga or flags["fadiga"]) else 0
            sede      = 1 if (sede or flags["sede_excessiva"]) else 0
            vomitos   = 1 if (vomitos or flags["vomitos"]) else 0
            falta_ar  = 1 if (falta_ar or flags["falta_ar"]) else 0


        entrada = pd.DataFrame([[idade, sexo, temp, fc, pas, pad, sat,
                                 tosse, fadiga, sede, vomitos, falta_ar]], columns=COLS)

        probs = model.predict_proba(entrada)[0]
        classes = model.classes_
        idx = np.argsort(probs)[::-1]
        classes_sorted = [str(classes[i]) for i in idx]
        probs_sorted = [float(probs[i]) for i in idx]
        top3 = [{"label": classes_sorted[i], "prob": probs_sorted[i]} for i in range(min(3, len(classes_sorted)))]

        return jsonify({"ok": True, "classes": classes_sorted, "probs": probs_sorted, "top3": top3})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400

if __name__ == "__main__":
    app.run(debug=True)
