# assignar.py
import psycopg2
from datetime import datetime
import streamlit as st

# =========================
# Conexão com o banco (Supabase)
# =========================
def get_connection():
    pg = st.secrets["postgres"]
    conn = psycopg2.connect(
        host=pg["host"],
        port=pg["port"],
        dbname=pg["dbname"],
        user=pg["user"],
        password=pg["password"],
        sslmode=pg.get("sslmode", "require")
    )
    return conn

# =========================
# Funções
# =========================
def chamar_refresh():
    from novo import refresh_incidentes_db  
    refresh_incidentes_db()

def hora_esta_no_turno(turno):
    if turno.upper() == "DAY OFF":
        return False
    try:
        h_inicio, h_fim = turno.split(" - ")
        fmt = "%H:%M"
        agora = datetime.now().time()
        inicio = datetime.strptime(h_inicio, fmt).time()
        fim = datetime.strptime(h_fim, fmt).time()
        if inicio < fim:
            return inicio <= agora <= fim
        else:  
            return agora >= inicio or agora <= fim
    except:
        return False

def pessoa_menos_incidentes(fecha):
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT person, shift FROM shifts WHERE fecha = %s", (fecha,))
    resultados = cursor.fetchall()
    
    pessoas_ativas = [p for p, s in resultados if hora_esta_no_turno(s)]
    
    if not pessoas_ativas:
        return None
    
    contador_incidentes = {}
    for pessoa in pessoas_ativas:
        cursor.execute(
            "SELECT COUNT(*) FROM incidentes WHERE person = %s AND fecha = %s",
            (pessoa, fecha)
        )
        count = cursor.fetchone()[0]
        contador_incidentes[pessoa] = count
      
    pessoa_escolhida = min(contador_incidentes, key=contador_incidentes.get)
    
    return pessoa_escolhida

def convert_person_to_id(person_name):
    person_map = {
        "SE77162": "Imad",
        "SG02198": "Yago",
        "SE12996": "Jeirdel",
        "SE64365": "Leopoldo",
        "E583062": "Lucie",
        "SE10257": "Gustavo",
        "SF62252": "Manuel",
        "SF62255": "Agustin",
        "SE10259": "Laura",
        "E546999": "Catia",
        "E405028": "Sandra",
        "SG18763": "Andrea",
        "SG18764": "Eleonora",
        "SE09787": "Lucas",
        "SD70551": "Maria C",
        "SE06493": "Mario",
        "SD70553": "Denis",
        "E506886": "Albert"
    }
    inverted_map = {v: k for k, v in person_map.items()}
    return inverted_map.get(person_name, None)

def assigned_person_name(assigned_person_id):
    person_map = {
        "SE77162": "IMAD",
        "SG02198": "YAGO",
        "SE12996": "JEIRDEL",
        "SE64365": "LEOPOLDO",
        "E583062": "LUCIE",
        "SE10257": "GUSTAVO",
        "SF62252": "MANUEL PORTO",
        "SF62255": "AGUSTIN HUGO",
        "SE10259": "LAURA",
        "E546999": "CATIA MARLENE",
        "E405028": "SANDRA",
        "SG18763": "ANDREA",
        "SG18764": "ELEONORA",
        "SE09787": "LUCAS",
        "SD70551": "MARIA DEL VALLE",
        "SE06493": "MARIO",
        "SD70553": "DENIS",
        "E506886": "ALBERT PAUL"
    }
    return person_map.get(assigned_person_id, None)

def assign_incident_to_persona(incident_number, person_in_note):
    conn = get_connection()
    cursor = conn.cursor()
    
    fecha = datetime.now().date()

    cursor.execute("SELECT person, shift FROM shifts WHERE fecha = %s", (fecha,))
    resultados = cursor.fetchall()
    
    pessoas_ativas = [p for p, s in resultados if hora_esta_no_turno(s)]
    pessoas_ativas_upper = [p.upper() for p in pessoas_ativas]

    if person_in_note is None:
        nome = assigned_person_name(person_in_note)
        if nome in pessoas_ativas_upper:
            return person_in_note
    else: 
        pessoa = pessoa_menos_incidentes(fecha)

        if not pessoa:
            print("Nenhuma pessoa ativa no momento para assignar o incidente.")
            return None
        
        cursor.execute("SELECT id FROM shifts WHERE fecha=%s and person=%s", (fecha, pessoa))
        shift_ids = cursor.fetchall()
        if not shift_ids:
            print("Nenhum shift encontrado para essa pessoa.")
            return None

        cursor.execute(
            "INSERT INTO incidentes (person, fecha, shift_id, incident_number) VALUES (%s, %s, %s, %s) RETURNING id",
            (pessoa, fecha, shift_ids[0][0], incident_number)
        )
        new_id = cursor.fetchone()[0]
        conn.commit()
        return convert_person_to_id(pessoa)
