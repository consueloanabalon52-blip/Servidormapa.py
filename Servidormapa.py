from flask import Flask, request
import requests

app = Flask(__name__)

HEADERS = {"User-Agent": "AppReciclajeConsuelo/1.0"}

@app.route('/puntos_reciclaje', methods=['POST'])
def puntos_reciclaje():
    ciudad = request.form.get('ciudad')

    print(f"\n[BUSQUEDA] Ciudad recibida: {ciudad}")

    if not ciudad:
        return "FALTA_CIUDAD", 400

    # Paso 1: convertir el nombre de la ciudad en coordenadas (geocoding)
    try:
        geo_url = "https://nominatim.openstreetmap.org/search"
        params = {"q": ciudad, "format": "json", "limit": 1}
        geo_resp = requests.get(geo_url, params=params, headers=HEADERS, timeout=8)
        geo_data = geo_resp.json()
    except Exception as e:
        print(f"[ERROR] No se pudo geolocalizar la ciudad: {e}")
        return "ERROR_GEOLOCALIZACION", 500

    if not geo_data:
        print("[INFO] Ciudad no encontrada.")
        return "CIUDAD_NO_ENCONTRADA", 404

    lat = float(geo_data[0]["lat"])
    lon = float(geo_data[0]["lon"])
    print(f"[INFO] Coordenadas encontradas: {lat}, {lon}")

    # Paso 2: buscar puntos de reciclaje cerca de esas coordenadas (radio 5km)
    overpass_query = f"""
    [out:json][timeout:15];
    node["amenity"="recycling"](around:5000,{lat},{lon});
    out;
    """

    try:
        overpass_url = "https://overpass-api.de/api/interpreter"
        op_resp = requests.post(overpass_url, data={"data": overpass_query}, headers=HEADERS, timeout=30)
        op_data = op_resp.json()
    except Exception as e:
        print(f"[ERROR] No se pudo consultar Overpass: {e}")
        return "ERROR_CONSULTA_PUNTOS", 500

    elementos = op_data.get("elements", [])
    print(f"[INFO] Puntos encontrados: {len(elementos)}")

    if not elementos:
        return "SIN_PUNTOS_CERCANOS", 200

    # Armamos el texto en un formato simple:
    # lat,lon,nombre ; lat,lon,nombre ; lat,lon,nombre ...
    partes = []
    for el in elementos[:20]:  # limitamos a 20 para no sobrecargar
        nombre = el.get("tags", {}).get("name", "Punto de reciclaje")
        nombre = nombre.replace(",", " ").replace(";", " ")  # evitamos que el nombre rompa el formato
        partes.append(f"{el['lat']},{el['lon']},{nombre}")

    resultado = ";".join(partes)
    return resultado, 200

if __name__ == '__main__':
    print("Servidor de mapa de reciclaje encendido y escuchando...")
    app.run(host='0.0.0.0', port=5002, debug=True, use_reloader=False)