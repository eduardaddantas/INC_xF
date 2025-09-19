import streamlit as st
import psycopg2
from datetime import datetime
from calendar import monthrange
import threading
import time

# ==============================
# Configuração inicial
# ==============================
st.set_page_config(page_title="Incident Distribution", layout="wide")

# ===== Conexão com PostgreSQL =====
conn = psycopg2.connect(
    host="localhost",
    port="5432",
    database="incidentes_db",
    user="admin",
    password="admin"
)
cursor = conn.cursor()

# ===== Dados =====
pessoas = ["Gustavo", "Manuel", "Agustin", "Yago", "Laura", "Mario", "Denis",
           "Maria C", "Eleonora", "Sandra", "Lucas", "Catia",
           "Andrea", "Lucie", "Leopoldo", "Imad", "Jeirdel"]

MAX_INCIDENTES = 60
meses_es = ["Enero","Febrero","Marzo","Abril","Mayo","Junio",
            "Julio","Agosto","Septiembre","Octubre","Noviembre","Diciembre"]

# ==============================
# Funções auxiliares
# ==============================
def generar_dias_mes(ano, mes):
    num_dias = monthrange(ano, mes)[1]
    return [datetime(ano, mes, d).strftime("%Y-%m-%d") for d in range(1, num_dias+1)]

def carregar_incidentes(fecha):
    cursor.execute("SELECT person, incident_number FROM incidentes WHERE fecha = %s", (fecha,))
    return cursor.fetchall()

def inserir_incidente(person, fecha, numero):
    cursor.execute(
        "INSERT INTO incidentes (person, fecha, incident_number) VALUES (%s, %s, %s)",
        (person, fecha, numero)
    )
    conn.commit()

def remover_incidente(person, fecha, numero):
    cursor.execute(
        "DELETE FROM incidentes WHERE person=%s AND fecha=%s AND incident_number=%s",
        (person, fecha, numero)
    )
    conn.commit()

def carregar_shifts(fecha):
    cursor.execute("SELECT person, shift FROM shifts WHERE fecha = %s", (fecha,))
    return cursor.fetchall()

def atualizar_shift(person, fecha, inicio, fim):
    turno = f"{inicio} - {fim}"
    cursor.execute("SELECT id FROM shifts WHERE fecha=%s AND person=%s", (fecha, person))
    result = cursor.fetchone()
    if result:
        cursor.execute("UPDATE shifts SET shift=%s WHERE id=%s", (turno, result[0]))
    else:
        cursor.execute("INSERT INTO shifts (person, fecha, shift) VALUES (%s, %s, %s)", (person, fecha, turno))
    conn.commit()

# Simulação do monitor (thread dummy)
def monitor_servicenow(url, intervalo):
    while True:
        print(f"[Monitor] Consultando {url} ...")
        time.sleep(intervalo)

# ==============================
# Interface Web
# ==============================
st.title("📊 Incident Distribution")

tab1, tab2 = st.tabs(["📝 Incidentes", "⏰ Shifts"])

# ------------------------------
# Aba Incidentes
# ------------------------------
with tab1:
    col1, col2, col3 = st.columns(3)
    with col1:
        ano = st.selectbox("Ano", [2025, 2026, 2027], index=0)
    with col2:
        mes = st.selectbox("Mes", meses_es, index=datetime.now().month - 1)
    with col3:
        dias = generar_dias_mes(ano, meses_es.index(mes)+1)
        fecha = st.selectbox("Día", dias, index=datetime.now().day-1)

    st.subheader(f"📌 Incidentes en {fecha}")

    dados = carregar_incidentes(fecha)
    if dados:
        st.table(dados)
    else:
        st.info("Nenhum incidente registrado.")

    st.divider()

    st.subheader("➕ Añadir incidente")
    col1, col2 = st.columns(2)
    with col1:
        pessoa = st.selectbox("Persona", pessoas)
    with col2:
        numero_inc = st.text_input("Número do incidente")

    if st.button("Guardar incidente"):
        if pessoa and numero_inc:
            inserir_incidente(pessoa, fecha, numero_inc)
            st.success("Incidente guardado!")
            st.experimental_rerun()
        else:
            st.error("Preencha todos os campos.")

    st.divider()

    st.subheader("🗑️ Remover incidente")
    if dados:
        pessoa_del = st.selectbox("Persona (remover)", [d[0] for d in dados])
        inc_del = st.selectbox("Incidente", [d[1] for d in dados])
        if st.button("Remover"):
            remover_incidente(pessoa_del, fecha, inc_del)
            st.success("Incidente removido.")
            st.experimental_rerun()

# ------------------------------
# Aba Shifts
# ------------------------------
with tab2:
    col1, col2, col3 = st.columns(3)
    with col1:
        ano_s = st.selectbox("Ano (Shift)", [2025, 2026, 2027], index=0)
    with col2:
        mes_s = st.selectbox("Mes (Shift)", meses_es, index=datetime.now().month - 1)
    with col3:
        dias_s = generar_dias_mes(ano_s, meses_es.index(mes_s)+1)
        fecha_s = st.selectbox("Día (Shift)", dias_s, index=datetime.now().day-1)

    st.subheader(f"👥 Shifts em {fecha_s}")

    shifts = carregar_shifts(fecha_s)
    if shifts:
        st.table(shifts)
    else:
        st.info("Nenhum shift registrado.")

    st.divider()

    st.subheader("✏️ Alterar / adicionar shift")
    col1, col2, col3 = st.columns(3)
    with col1:
        pessoa_s = st.selectbox("Persona", pessoas)
    with col2:
        inicio = st.text_input("Hora inicio (HH:MM)", "09:00")
    with col3:
        fim = st.text_input("Hora fim (HH:MM)", "17:00")

    if st.button("Guardar shift"):
        if pessoa_s and inicio and fim:
            atualizar_shift(pessoa_s, fecha_s, inicio, fim)
            st.success("Shift atualizado.")
            st.experimental_rerun()
        else:
            st.error("Preencha todos os campos.")

# ------------------------------
# Monitor (thread dummy)
# ------------------------------
if st.sidebar.button("▶️ Iniciar monitor ServiceNow"):
    t = threading.Thread(target=monitor_servicenow, args=("https://fiatchrysler.service-now.com/", 60), daemon=True)
    t.start()
    st.sidebar.success("Monitor iniciado em background (ver logs do servidor).")
