import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from assignar import assign_incident_to_persona, assigned_person_name


import time

CHROME_DRIVER_PATH =r"chromedriver.exe"

# Mapa de IDs → nomes para o lookup
assigned_person_map = {
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

work_notes_persona_map = {
    "ALBERT PAUL ALAEZ VAZQUEZ": "E506886",
    "YAGO CASCALLAR": "SG02198",
    "JEIRDEL GOES COSTA": "SE12996",
    "LEOPOLDO DOMINGUEZ AMIGO": "SE64365",
    "LUCIE PITHARDOVA": "E583062",
    "GUSTAVO FANTAUZZI GONZLEZ": "SE10257",
    "MANUEL PORTO JORGE": "SF62252",
    "AGUSTIN HUGO GOMEZ": "SF62255",
    "LAURA CORDEIRO SOBRINO": "SE10259",
    "CATIA MARLENE DA SILVA RODRIGUES": "E546999",
    "SANDRA RODRIGUES FERNANDES": "E405028",
    "ANDREA VIEITEZ": "SG18763",
    "ELEONORA VERNASCA": "SG18764",
    "LUCAS ALVES MACEDO": "SE09787",
    "MARIA DEL VALLE RUIZ CASALDERREY": "SD70551",
    "MARIO CONDE BANOS": "SE06493",
    "DENIS OTERO RIVEIRO": "SD70553"
}

def monitor_servicenow_incidents(URL_DASHBOARD, refresh_interval=60):
    print("🚀 Starting clean Google Chrome with Selenium...")

    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--no-first-run")
    chrome_options.add_argument("--no-default-browser-check")
    chrome_options.add_argument("--disable-popup-blocking")
    chrome_options.add_argument("--disable-features=IsolateOrigins,site-per-process")
    chrome_options.add_experimental_option("prefs", {
        "profile.default_content_setting_values.popups": 1,
        "profile.default_content_setting_values.automatic_downloads": 1,
        "profile.default_content_setting_values.notifications": 1,
        "profile.default_content_setting_values.multiple-automatic-downloads": 1
    })

    service = Service(executable_path=CHROME_DRIVER_PATH)
    driver = webdriver.Chrome(service=service, options=chrome_options)

    wait = WebDriverWait(driver, 30)
    last_incident = None

    try:
        driver.get(URL_DASHBOARD)
        print("🌐 Dashboard opened.")
        time.sleep(5)

        while True:
            driver.refresh()
            print(f"🔄 Dashboard refreshed. Waiting {refresh_interval}s...")

            driver.switch_to.default_content()
            try:
                wait.until(EC.frame_to_be_available_and_switch_to_it("gsft_main"))
                print("📂 Switched to 'gsft_main' iframe.")

                try:
                    driver.find_element(By.XPATH, "//td[contains(text(),'No records to display')]")
                    print("⚠️ No incidents available. Waiting 15s...")
                    time.sleep(15)
                    continue
                except NoSuchElementException:
                    pass

                incident_link = wait.until(EC.element_to_be_clickable((
                    By.XPATH, "(//a[contains(@class, 'linked') and contains(@class, 'formlink')])[1]"
                )))
                incident_number = incident_link.text.strip()
                print(f"🔎 Found incident: {incident_number}")

                if incident_number == last_incident:
                    print("⏳ Same incident detected, waiting...")
                    time.sleep(15)
                    continue

                driver.execute_script("arguments[0].scrollIntoView(true);", incident_link)
                incident_link.click()
                print(f"✅ Opened incident: {incident_number}")
                last_incident = incident_number

                try:
                    description_field = wait.until(
                        EC.presence_of_element_located((By.ID, "incident.short_description"))
                    )
                    description_text = description_field.get_attribute("value").strip()
           
                    if "PAMIR" in description_text:
                        print(f"🚫 Incidente {incident_number} ignorado (PAMIR detectado).")
                        last_incident = incident_number  

                       
                        try:
                            from script import adicionar_incidente_manual
                            adicionar_incidente_manual(incident_number)
                        except Exception as e:
                            print(f"⚠️ Não consegui adicionar o incidente manual: {e}")

                            driver.back()
                            time.sleep(5)
                            continue

                except Exception as e:
                    print(f"⚠️ Não consegui verificar a descrição: {e}")

                # ---- Filtro Work Notes ----
                try:
                    activity_filter_button = wait.until(
                        EC.element_to_be_clickable((By.ID, "activity_field_filter_button"))
                    )
                    driver.execute_script("arguments[0].scrollIntoView(true);", activity_filter_button)
                    activity_filter_button.click()
                    print("✅ Cliquei no botão de filtro de atividade")
                    time.sleep(5)

                    wait.until(EC.visibility_of_element_located((By.ID, "activity_field_filter_popover")))
                    print("✅ Popover do filtro carregado")
                    time.sleep(5)

                    try:
                        checkbox = wait.until(
                            EC.presence_of_element_located((By.ID, "activity_filter.work_notes"))
                        )
                        driver.execute_script("arguments[0].scrollIntoView(true);", checkbox)

                        if not checkbox.is_selected():
                            try:
                                checkbox.click()
                            except:
                                driver.execute_script("arguments[0].click();", checkbox)
                            print("✅ Selecionado: Work notes")
                        else:
                            print("ℹ️ Já estava selecionado: Work notes")

                    except Exception as e:
                        print("⚠️ Checkbox 'Work notes' não encontrado:", e)
                
                    work_notes = driver.find_elements(By.CSS_SELECTOR, "span.sn-card-component-createdby")

                    top_item = None 

                    for item in work_notes:
                        if item.text.strip() in work_notes_persona_map: 
                            top_item = item
                            top_item.click()
                            break  
                    if top_item:  
                        person_in_note = work_notes_persona_map.get(top_item.text.strip())
                        print(f"Pessoa na nota: {person_in_note}")
                    else:
                        print("Nenhuma nota correspondeu ao mapa de personas.")
                except Exception as e:
                    print("❌ Erro ao interagir com o filtro de atividade:", e)

               
                try:
                    print("📝 Assigning incident to persona...")
                    assigned_person_id = assign_incident_to_persona(incident_number, person_in_note)
                    print(f"Assigned ID: {assigned_person_id}")

                except Exception as e:
                    print(f"❌ Error in assign_incident_to_persona: {e}")
                    assigned_person_id = None

                print(f"Pessoa assignada {assigned_person_id}")

                if assigned_person_id:
                    person_name = assigned_person_map.get(assigned_person_id)
                    if not person_name:
                        print(f"⚠️ ID '{assigned_person_id}' não encontrado no mapa")
                    else:
                        try:
                            lookup_button = wait.until(EC.element_to_be_clickable((
                                By.XPATH, "//button[contains(@id,'lookup.incident.assigned_to')]"
                            )))

                            before_windows = driver.window_handles
                            lookup_button.click()
                            print("🖱️ Cliquei no botão 'Lookup Affected User'.")
                            time.sleep(2)

                            after_windows = driver.window_handles
                            new_window = [w for w in after_windows if w not in before_windows]

                            if new_window:
                                driver.switch_to.window(new_window[0])
                                print("✅ Lookup abriu em nova janela")
                            else:
                                print("ℹ️ Lookup abriu no mesmo separador")

                            search_box = wait.until(EC.presence_of_element_located((
                                By.XPATH, "//input[@type='search' and contains(@id,'_text')]"
                            )))
                            search_box.clear()
                            search_box.send_keys(assigned_person_id)
                            search_box.send_keys(Keys.RETURN)
                            print(f"🔎 Pesquisado User ID '{assigned_person_id}'.")
                            time.sleep(2)

                            results = driver.find_elements(By.CSS_SELECTOR, "a.glide_ref_item_link")
                            print(results[0].text)
                        
                            if results:
                                top_item = results[0]
                                top_item.click()
                                  
                            driver.switch_to.default_content()
                            wait.until(EC.frame_to_be_available_and_switch_to_it("gsft_main"))
                            print("📂 Reentrei no iframe 'gsft_main'")

                         
                            assigned_field = wait.until(
                                EC.presence_of_element_located((By.ID, "sys_display.incident.assigned_to"))
                            )
                            WebDriverWait(driver, 10).until(
                                lambda d: assigned_person_name.lower() in assigned_field.get_attribute("value").lower()
                            )
                            value = assigned_field.get_attribute("value")
                            print(f"✅ Campo 'Assigned to' preenchido com: {value}")

                            #try:
                            #    update_button = wait.until(
                            #        EC.element_to_be_clickable((By.ID, "sysverb_update"))
                            #    )
                            #    driver.execute_script("arguments[0].scrollIntoView(true);", update_button)
                            #    update_button.click()
                            #    print("💾 Incident atualizado com sucesso (Update).")
                            #    time.sleep(3)  # dar tempo para o ServiceNow processar
                            #except TimeoutException:
                            #    print("❌ Botão 'Update' não encontrado a tempo.")
                            #except Exception as e:
                            #    print(f"⚠️ Erro ao tentar dar Update no incidente: {e}")


                        except TimeoutException:
                            print("❌ Erro: Lookup button ou elementos não encontrados.")
                        except Exception as e:
                            print(f"❌ Erro inesperado no assign: {e}")

                print(f"🕑 Waiting {refresh_interval}s before next refresh...\n")
                time.sleep(refresh_interval)

            except (TimeoutException, NoSuchElementException) as e:
                print(f"⚠️ Frame or element access error: {e}. Retrying in 15s...")
                time.sleep(15)
                continue

    except KeyboardInterrupt:
        print("🛑 Execution interrupted by user.")

    finally:
        print("🧹 Closing the browser.")
        driver.quit()
