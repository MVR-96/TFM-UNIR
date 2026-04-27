import time
import csv
from kubernetes import client, config
from datetime import datetime

# Configuración de Kubernetes
config.load_kube_config()
v1 = client.AppsV1Api()
core_v1 = client.CoreV1Api()

NAMESPACE = "tfm-app"
DEPLOYMENT_NAME = "nginx-demo"
OUTPUT_FILE = "resultados_tfm.csv"

def wait_for_recovery(expected_replicas=2):
    """Mide el tiempo hasta que el deployment vuelve al estado deseado"""
    start_time = time.time()
    while True:
        try:
            dep = v1.read_namespaced_deployment(DEPLOYMENT_NAME, NAMESPACE)
            if dep.status.ready_replicas == expected_replicas:
                end_time = time.time()
                return round(end_time - start_time, 2)
        except Exception:
            pass # Ignorar errores momentáneos durante el borrado
        time.sleep(1)

def run_experiment(scenario_name, action_fn):
    print(f"--- Iniciando {scenario_name} ---")
    action_fn()
    duration = wait_for_recovery()
    print(f"Recuperado en: {duration}s")
    
    # Guardar en CSV
    with open(OUTPUT_FILE, 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([datetime.now(), scenario_name, duration])

# --- Definición de los Desastres ---

def scenario_a_drift():
    # Escalar manualmente a 5
    body = {"spec": {"replicas": 5}}
    v1.patch_namespaced_deployment(DEPLOYMENT_NAME, NAMESPACE, body)

def scenario_b_rto():
    # Borrar el deployment
    v1.delete_namespaced_deployment(DEPLOYMENT_NAME, NAMESPACE)

# --- Ejecución del Experimento (Ejemplo: 30 veces) ---

# Encabezado del CSV
with open(OUTPUT_FILE, 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(["Timestamp", "Escenario", "Tiempo_Recuperacion_S"])

for i in range(30):
    print(f"Iteración {i+1}/30")
    run_experiment("Escenario_A_Drift", scenario_a_drift)
    time.sleep(10) # Pausa para estabilización
    run_experiment("Escenario_B_RTO", scenario_b_rto)
    time.sleep(10)

print("¡Experimento completado! Los datos están en resultados_tfm.csv")