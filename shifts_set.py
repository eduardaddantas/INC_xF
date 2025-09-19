import psycopg2
from datetime import date, timedelta

# Configuração de turnos por pessoa
turnos_pessoas = {
    "Gustavo": {"Lunes": "06:00 - 14:30", "Martes": "06:00 - 14:30", "Miércoles": "06:00 - 14:30",
                "Jueves": "06:00 - 14:30", "Viernes": "06:00 - 14:30", "Sábado": "DAY OFF", "Domingo": "DAY OFF"},
    "Manuel": {"Lunes": "06:00 - 14:30", "Martes": "06:00 - 14:30", "Miércoles": "06:00 - 14:30",
               "Jueves": "06:00 - 14:30", "Viernes": "06:00 - 14:30", "Sábado": "DAY OFF", "Domingo": "DAY OFF"},
    "Agustin": {"Lunes": "08:00 - 17:00", "Martes": "08:00 - 17:00", "Miércoles": "08:00 - 17:00",
                "Jueves": "08:00 - 17:00", "Viernes": "08:00 - 17:00", "Sábado": "DAY OFF", "Domingo": "DAY OFF"},
    "Yago": {"Lunes": "09:00 - 18:00", "Martes": "09:00 - 18:00", "Miércoles": "09:00 - 18:00",
             "Jueves": "09:00 - 18:00", "Viernes": "09:00 - 18:00", "Sábado": "DAY OFF", "Domingo": "DAY OFF"},
    "Laura": {"Lunes": "06:00 - 14:30", "Martes": "06:00 - 14:30", "Miércoles": "06:00 - 14:30",
              "Jueves": "06:00 - 14:30", "Viernes": "06:00 - 14:30", "Sábado": "DAY OFF", "Domingo": "DAY OFF"},
    "Mario": {"Lunes": "13:30 - 22:00", "Martes": "13:30 - 22:00", "Miércoles": "13:30 - 22:00",
              "Jueves": "13:30 - 22:00", "Viernes": "13:30 - 22:00", "Sábado": "DAY OFF", "Domingo": "DAY OFF"},
    "Denis": {"Lunes": "14:00 - 22:30", "Martes": "14:00 - 22:30", "Miércoles": "14:00 - 22:30",
              "Jueves": "14:00 - 22:30", "Viernes": "14:00 - 22:30", "Sábado": "DAY OFF", "Domingo": "DAY OFF"},
    "Maria C": {"Lunes": "13:30 - 22:00", "Martes": "13:30 - 22:00", "Miércoles": "13:30 - 22:00",
                "Jueves": "13:30 - 22:00", "Viernes": "13:30 - 22:00", "Sábado": "DAY OFF", "Domingo": "DAY OFF"},
    "Eleonora": {"Lunes": "13:30 - 22:00", "Martes": "13:30 - 22:00", "Miércoles": "13:30 - 22:00",
                 "Jueves": "13:30 - 22:00", "Viernes": "13:30 - 22:00", "Sábado": "DAY OFF", "Domingo": "DAY OFF"},
    "Sandra": {"Lunes": "11:00 - 20:00", "Martes": "11:00 - 20:00", "Miércoles": "11:00 - 20:00",
               "Jueves": "11:00 - 20:00", "Viernes": "11:00 - 20:00", "Sábado": "DAY OFF", "Domingo": "DAY OFF"},
    "Lucas": {"Lunes": "13:30 - 22:00", "Martes": "13:30 - 22:00", "Miércoles": "13:30 - 22:00",
              "Jueves": "13:30 - 22:00", "Viernes": "13:30 - 22:00", "Sábado": "DAY OFF", "Domingo": "DAY OFF"},
    "Catia": {"Lunes": "09:30 - 18:30", "Martes": "09:30 - 18:30", "Miércoles": "09:30 - 18:30",
              "Jueves": "09:30 - 18:30", "Viernes": "09:30 - 18:30", "Sábado": "DAY OFF", "Domingo": "DAY OFF"},
    "Andrea": {"Lunes": "21:30 - 06:00", "Martes": "21:30 - 06:00", "Miércoles": "21:30 - 06:00",
               "Jueves": "21:30 - 06:00", "Viernes": "21:30 - 06:00", "Sábado": "DAY OFF", "Domingo": "DAY OFF"},
    "Lucie": {"Lunes": "21:30 - 06:00", "Martes": "21:30 - 06:00", "Miércoles": "21:30 - 06:00",
              "Jueves": "21:30 - 06:00", "Viernes": "21:30 - 06:00", "Sábado": "DAY OFF", "Domingo": "DAY OFF"},
    "Leopoldo": {"Lunes": "21:30 - 06:00", "Martes": "21:30 - 06:00", "Miércoles": "21:30 - 06:00",
                 "Jueves": "21:30 - 06:00", "Viernes": "21:30 - 06:00", "Sábado": "DAY OFF", "Domingo": "DAY OFF"},
    "Imad": {"Lunes": "DAY OFF", "Martes": "DAY OFF", "Miércoles": "08:00 - 17:00",
             "Jueves": "08:00 - 17:00", "Viernes": "DAY OFF", "Sábado": "08:00 - 17:00", "Domingo": "08:00 - 17:00"},
    "Jeirdel": {"Lunes": "DAY OFF", "Martes": "DAY OFF", "Miércoles": "13:00 - 21:30",
                "Jueves": "13:00 - 21:30", "Viernes": "DAY OFF", "Sábado": "13:00 - 21:30", "Domingo": "13:00 - 21:30"}
}

# Mapear os índices do Python para os dias em espanhol
dias_semana_python = {
    0: "Lunes",
    1: "Martes",
    2: "Miércoles",
    3: "Jueves",
    4: "Viernes",
    5: "Sábado",
    6: "Domingo"
}


def get_connection():
    return psycopg2.connect(
        host="localhost",   # se rodar no Windows fora do Docker
        port="5432",
        database="incidentes_db",   # aqui estava escrito errado: "datebase"
        user="admin",
        password="admin"
    )


# Inserir todos os shifts para todas as pessoas
def inserir_shifts_todas_pessoas(year, turnos):
    conn = get_connection()
    cur = conn.cursor()

    for person, turnos_por_dia in turnos.items():
        date_atual = date(year, 1, 1)
        date_final = date(year, 12, 31)

        while date_atual <= date_final:
            weekday_index = date_atual.weekday()
            weekday = dias_semana_python[weekday_index]
            turno = turnos_por_dia[weekday]

            cur.execute("""
                INSERT INTO shifts (person, date, weekday, shift)
                VALUES (%s, %s, %s, %s)
            """, (person, date_atual, weekday, turno))

            date_atual += timedelta(days=1)

        print(f"✅ Shifts inseridos para {person}")

    conn.commit()
    cur.close()
    conn.close()
    print("🎉 Todos os shifts inseridos para o ano!")

# ======================
# Execução
# ======================
if __name__ == "__main__":
    inserir_shifts_todas_pessoas(2025, turnos_pessoas)
