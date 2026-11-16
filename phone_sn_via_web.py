import ipaddress
import unicodedata
from datetime import datetime

import requests
from bs4 import BeautifulSoup


def recorrer_red(red_str):
    """
    Recorre una red dada en notación CIDR (ej: '192.168.1.0/24')
    y devuelve una lista con todas las direcciones de host.
    """
    red = ipaddress.ip_network(red_str)
    return [str(ip) for ip in red.hosts()]


def normalizar_texto(texto):
    """Normaliza cadenas para comparar etiquetas independientemente de tildes y signos."""
    if texto is None:
        return ""

    texto = texto.replace("\xa0", " ").strip()
    texto = unicodedata.normalize("NFKD", texto)
    texto = texto.encode("ascii", "ignore").decode("ascii")
    texto = texto.lower()
    texto = "".join(caracter for caracter in texto if caracter.isalnum() or caracter.isspace())
    return " ".join(texto.split())


def extraer_datos_telefono(html):
    """Extrae version, serial y model desde HTML del teléfono con etiquetas en español o inglés."""
    soup = BeautifulSoup(html, "html.parser")
    filas = soup.find_all("tr")

    datos = {"version": None, "serial": None, "model": None}

    for fila in filas:
        celdas = [celda.get_text(" ", strip=True) for celda in fila.find_all("td")]
        if len(celdas) < 2:
            continue

        campo = normalizar_texto(celdas[0])
        valor = celdas[-1].strip()

        if not valor:
            continue

        if campo in {"version", "id de carga de aplicacion", "id de carga de aplicacion software"}:
            datos["version"] = valor
        elif campo in {"numero de serie", "n de serie", "nro de serie", "n de serie"}:
            datos["serial"] = valor
        elif campo in {"numero de modelo", "n de modelo", "nro de modelo", "n de modelo"}:
            datos["model"] = valor
        elif campo == "serial number":
            datos["serial"] = valor
        elif campo == "model number":
            datos["model"] = valor
        elif campo == "version number":
            datos["version"] = valor

    return datos


def guardar_log(texto, archivo="registro_de_logs.txt"):
    """
    Guarda un texto en un archivo de logs con fecha y hora.
    """
    fecha_hora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    with open(archivo, "a", encoding="utf-8") as file:
        file.write(f"[{fecha_hora}] {texto}\n")


def leer_ips_desde_txt(ruta_archivo):
    """Lee una lista de IPs desde un archivo .txt, ignorando líneas vacías y comentarios."""
    ips = []
    with open(ruta_archivo, "r", encoding="utf-8") as archivo:
        for linea in archivo:
            ip = linea.strip()
            if ip and not ip.startswith("#"):
                ips.append(ip)
    return ips


if __name__ == "__main__":
    ips = leer_ips_desde_txt("CUCM/ips.txt")

    for ip in ips:
        url = f"http://{ip}/"
        try:
            response = requests.get(url, timeout=2)

            if response.status_code == 200:
                datos = extraer_datos_telefono(response.text)
                resultado = (
                    f"IP: {ip} | Version: {datos['version']} | "
                    f"Serial: {datos['serial']} | Model: {datos['model']}"
                )
                print(resultado)
                guardar_log(resultado)

            else:
                error_msg = f"{url} -> Error HTTP {response.status_code}"
                print(error_msg)
                guardar_log(error_msg)

        except requests.exceptions.RequestException as e:
            error_msg = f"{url} -> Error: {e}"
            print(error_msg)
            guardar_log(error_msg)
