import tkinter as tk
from tkinter import ttk, simpledialog, messagebox
import customtkinter
from datetime import datetime
from calendar import monthrange
import locale
import threading
import psycopg2
from monitor import monitor_servicenow_incidents

locale.setlocale(locale.LC_TIME, "es_ES")
URL_DASHBOARD = "https://fiatchrysler.service-now.com/nav_to.do?uri=$pa_dashboard.do%3Fsysparm_dashboard%3D04e8474647566e1001e78ba5536d4349%26sysparm_tab%3De75d12d447266e505a95bce5536d43d5%26sysparm_cancelable%3Dtrue%26sysparm_editable%3Dfalse%26sysparm_active_panel%3Dfalse"
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

dias_semana_es = ["Lunes","Martes","Miércoles","Jueves","Viernes","Sábado","Domingo"]

# ===== Funções =====
def mostrar_frame(frame):
    frame.tkraise()

def actualizar_incidentes_periodicamente():
    actualizar_incidentes()
    ventana.after(60000, actualizar_incidentes_periodicamente)

def iniciar_monitor_servicenow():
    t = threading.Thread(target=monitor_servicenow_incidents, args=(URL_DASHBOARD, 60), daemon=True)
    t.start()
    messagebox.showinfo("Info", "Monitor ServiceNow iniciado em background.")

def generar_dias_semana_mes(ano, mes):
    num_dias = monthrange(ano, mes)[1]
    dias = [datetime(ano, mes, d) for d in range(1,num_dias+1)]
    return [(d.strftime("%Y-%m-%d"), dias_semana_es[d.weekday()]) for d in dias]

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

def cargar_incidentes_db():
    global incidentes
    incidentes = {person:[] for person in pessoas}
    cursor.execute("SELECT person, fecha, incident_number FROM incidentes")
    for person, fecha, incident_number in cursor.fetchall():
        if person in pessoas:
            incidentes[person].append((incident_number, fecha))

def refresh_incidentes_db():
    for item in tabla_incidentes.get_children():
        tabla_incidentes.delete(item)
    
    cursor.execute("SELECT id, person, fecha, incident_number FROM incidentes ORDER BY id DESC")

    for row in cursor.fetchall():
        tabla_incidentes.insert("", "end", values=row)

def actualizar_incidentes():
    for i in tabla_incidentes.get_children():
        tabla_incidentes.delete(i)

    if not combo_dia.get():
        return

    dia_idx = int(combo_dia.get()) - 1
    fecha = dias_mes[dia_idx][0]

    cursor.execute("SELECT person, shift FROM shifts WHERE fecha = %s", (fecha,))
    resultados = cursor.fetchall()
    pessoas_com_turno = {row[0]: row[1] for row in resultados if row[0] in pessoas}

    pessoas_ativas = [p for p, s in pessoas_com_turno.items() if hora_esta_no_turno(s)]

    tabla_incidentes["columns"] = ["#"] + pessoas_ativas  

    tabla_incidentes.heading("#", text="#", anchor="center")
    tabla_incidentes.column("#", width=50, anchor="center")

    for person in pessoas_ativas:
        turno = pessoas_com_turno[person]
        tabla_incidentes.heading(person, text=f"{person} ({turno})", anchor="center")
        tabla_incidentes.column(person, width=200, anchor="center")

    lista_por_person = []
    for person in pessoas_ativas:
        cursor.execute("SELECT id FROM shifts WHERE fecha = %s and person = %s", (fecha,person))
        ids = cursor.fetchall()
        for id in ids:
            cursor.execute("SELECT incident_number FROM incidentes WHERE shift_id = %s", (id[0],))
            incs_db = [row[0] for row in cursor.fetchall()]
            for inc in incs_db:
                if (inc, fecha) not in incidentes[person]:
                    incidentes[person].append((inc, fecha))

        incs = [inc for inc, f in incidentes.get(person, []) if f == fecha]
        incs += [""] * (MAX_INCIDENTES - len(incs))
        lista_por_person.append(incs[:MAX_INCIDENTES])

    for i in range(MAX_INCIDENTES):
        fila = [i+1]  
        for j in range(len(pessoas_ativas)):
            fila.append(lista_por_person[j][i])
        item_id = tabla_incidentes.insert("", "end", values=fila)
        for j, person in enumerate(pessoas_ativas):
            turno = pessoas_com_turno[person]
            if hora_esta_no_turno(turno):
                tabla_incidentes.item(item_id, tags=("ativo",))

def editar_celda(event):
    region = tabla_incidentes.identify("region", event.x, event.y)
    if region != "cell":
        return
    columna = tabla_incidentes.identify_column(event.x)
    fila_id = tabla_incidentes.identify_row(event.y)
    if not fila_id:
        return
    col_idx = int(columna.replace("#","")) - 1
    person = tabla_incidentes["columns"][col_idx]
    
    dia_idx = int(combo_dia.get()) - 1
    fecha = dias_mes[dia_idx][0]

    cursor.execute("SELECT id FROM shifts WHERE fecha = %s and person = %s", (fecha, person))
    shift_ids = cursor.fetchall()
    

    inc_actual = tabla_incidentes.set(fila_id, person)
    nuevo_inc = simpledialog.askstring("Editar Incidente", f"{person} em {fecha}:", initialvalue=inc_actual)
    
    if nuevo_inc is None:
        return  
    elif nuevo_inc == "":
        cursor.execute("DELETE FROM incidentes WHERE person=%s AND fecha=%s AND incident_number=%s",
                       (person, fecha, inc_actual))
        conn.commit()
        incidentes[person] = [(inc, f) for inc, f in incidentes[person] if not (inc == inc_actual and f == fecha)]
    else:
            incidentes[person].append((nuevo_inc, fecha))
            cursor.execute(
                "INSERT INTO incidentes (person, fecha, shift_id, incident_number) VALUES (%s, %s, %s, %s) RETURNING id",
                (person, fecha, shift_ids[0][0], nuevo_inc)
            )
            cursor.fetchone()
            conn.commit()
    actualizar_incidentes()

def cambiar_mes_ano(event=None):
    global dias_mes
    mes = meses_es.index(combo_mes_inc.get())+1
    ano = int(combo_ano_inc.get())
    dias_mes = generar_dias_semana_mes(ano, mes)
    combo_dia["values"] = [str(i+1) for i in range(len(dias_mes))]
    if not combo_dia.get() or int(combo_dia.get()) > len(dias_mes):
        combo_dia.set("1")
    actualizar_incidentes()

import customtkinter
from tkinter import ttk, messagebox
from datetime import datetime

# ===== Interface =====
ventana = customtkinter.CTk()
ventana.title("Incident Distribution")  
ventana.geometry("1200x500")
ventana.state("zoomed")

# ===== Estilo moderno (CustomTkinter) =====
customtkinter.set_appearance_mode("System") 
customtkinter.set_default_color_theme("metal.json")

style = ttk.Style()

# Cabeçalhos maiores
style.configure("Treeview.Heading", font=("Segoe UI", 14, "bold"), padding=(10, 12, 10, 12))

# Linhas maiores
style.configure("Treeview", font=("Segoe UI", 12), rowheight=32) 

# ===== Frames =====
frame_incidentes = customtkinter.CTkFrame(ventana, corner_radius=10)
frame_incidentes.place(relwidth=1, relheight=1)

frame_top_inc = customtkinter.CTkFrame(frame_incidentes)
frame_top_inc.pack(pady=5)

customtkinter.CTkLabel(frame_top_inc, text="Dia:").pack(side="left", padx=(5,2))
combo_dia = customtkinter.CTkComboBox(frame_top_inc, values=[], width=70)
combo_dia.pack(side="left", padx=10)

customtkinter.CTkLabel(frame_top_inc, text="Mes:").pack(side="left", padx=(5,2))
combo_mes_inc = customtkinter.CTkComboBox(frame_top_inc, values=meses_es, width=120)
combo_mes_inc.pack(side="left", padx=10)

customtkinter.CTkLabel(frame_top_inc, text="Año:").pack(side="left", padx=(5,2))
combo_ano_inc = customtkinter.CTkComboBox(frame_top_inc, values=[str(y) for y in range(2025, 2031)], width=90)
combo_ano_inc.pack(side="left", padx=10)

btn_monitor = customtkinter.CTkButton(frame_top_inc, text="Asignación automática", command=iniciar_monitor_servicenow)
btn_monitor.pack(side="left", padx=9)

btn_cambiar_shift = customtkinter.CTkButton(frame_top_inc, text="Cambiar Shift", command=lambda: mostrar_frame(frame_cambiar_shift))
btn_cambiar_shift.pack(side="right", padx=10)

combo_mes_inc.bind("<<ComboboxSelected>>", cambiar_mes_ano)
combo_ano_inc.bind("<<ComboboxSelected>>", cambiar_mes_ano)
combo_dia.bind("<<ComboboxSelected>>", lambda e: actualizar_incidentes())

# ===== Tabla (Treeview permanece) =====
tabla_incidentes = ttk.Treeview(frame_incidentes, columns=[], show='headings')
tabla_incidentes.pack(fill="both", expand=True, padx=10, pady=10)

# ===== Frame Cambiar Shift =====
frame_cambiar_shift = customtkinter.CTkFrame(ventana, corner_radius=10)
frame_cambiar_shift.place(relwidth=1, relheight=1)

frame_top_cambiar = customtkinter.CTkFrame(frame_cambiar_shift)
frame_top_cambiar.pack(pady=5)

btn_voltar = customtkinter.CTkButton(frame_top_cambiar, fg_color="transparent", border_width=2, text_color=("gray10", "#DCE4EE"), text="Voltar", command=lambda: mostrar_frame(frame_incidentes))
btn_voltar.pack(side="left", padx=10)

customtkinter.CTkLabel(frame_top_cambiar, text="Persona:").pack(side="left", padx=2)
combo_persona = customtkinter.CTkComboBox(frame_top_cambiar, values=pessoas, width=150)
combo_persona.pack(side="left", padx=5)

customtkinter.CTkLabel(frame_top_cambiar, text="Dia:").pack(side="left", padx=2)
combo_dia_shift = customtkinter.CTkComboBox(frame_top_cambiar, values=[str(i+1) for i in range(1,32)], width=70)
combo_dia_shift.pack(side="left", padx=5)

customtkinter.CTkLabel(frame_top_cambiar, text="Mes:").pack(side="left", padx=2)
combo_mes_shift = customtkinter.CTkComboBox(frame_top_cambiar, values=meses_es, width=120)
combo_mes_shift.pack(side="left", padx=5)

customtkinter.CTkLabel(frame_top_cambiar, text="Año:").pack(side="left", padx=2)
combo_ano_shift = customtkinter.CTkComboBox(frame_top_cambiar, values=[str(y) for y in range(2025, 2031)], width=90)
combo_ano_shift.pack(side="left", padx=5)

customtkinter.CTkLabel(frame_cambiar_shift, text="Hora inicio (HH:MM):").pack(pady=5)
entry_inicio = customtkinter.CTkEntry(frame_cambiar_shift, width=120)
entry_inicio.pack(pady=5)

customtkinter.CTkLabel(frame_cambiar_shift, text="Hora fim (HH:MM):").pack(pady=5)
entry_fim = customtkinter.CTkEntry(frame_cambiar_shift, width=120)
entry_fim.pack(pady=5)

def alterar_shift():
    persona = combo_persona.get()
    dia = int(combo_dia_shift.get())
    mes = meses_es.index(combo_mes_shift.get()) + 1
    ano = int(combo_ano_shift.get())
    fecha = datetime(ano, mes, dia).strftime("%Y-%m-%d")
    inicio = entry_inicio.get()
    fim = entry_fim.get()
    
    if not persona or not inicio or not fim:
        messagebox.showerror("Error", "Todos los campos son obligatorios")
        return
    
    cursor.execute("SELECT id FROM shifts WHERE fecha=%s AND person=%s", (fecha, persona))
    result = cursor.fetchone()
    
    if result:
        cursor.execute("UPDATE shifts SET shift=%s WHERE id=%s", (f"{inicio} - {fim}", result[0]))
    else:
        cursor.execute("INSERT INTO shifts (person, fecha, shift) VALUES (%s, %s, %s)", (persona, fecha, f"{inicio} - {fim}"))
    
    conn.commit()
    messagebox.showinfo("Éxito", f"Shift de {persona} para {fecha} actualizado.")
    cargar_incidentes_db()
    actualizar_incidentes()
    mostrar_frame(frame_incidentes)

btn_alterar = customtkinter.CTkButton(frame_cambiar_shift, text="Alterar", command=alterar_shift)
btn_alterar.pack(pady=10)

# ===== Inicialização =====
hoy = datetime.now()
dias_mes = generar_dias_semana_mes(hoy.year, hoy.month)
combo_mes_inc.set(meses_es[hoy.month - 1])
combo_ano_inc.set(hoy.year)
combo_dia.configure(values=[str(i+1) for i in range(len(dias_mes))])
combo_dia.set(hoy.day)

cargar_incidentes_db()
actualizar_incidentes()
actualizar_incidentes_periodicamente() 

tabla_incidentes.bind("<Double-1>", editar_celda)
mostrar_frame(frame_incidentes)

ventana.mainloop()
