from flask import Flask, json, request
from pymongo import MongoClient

USER = "grupo32"
PASS = "grupo32"
DATABASE = "grupo32"

URL = f"mongodb://{USER}:{PASS}@gray.ing.puc.cl/{DATABASE}?authSource=admin"
client = MongoClient(URL)

USER_KEYS = ['uid', 'name', 'description', 'age']
MENSAJES_KEYS = ['mid', 'message', 'sender', 'receptant', 'lat', 'long', 'date']

# Base de datos del grupo
db = client["grupo32"]

# Seleccionamos la collección de usuarios
usuarios = db.usuarios
mensajes = db.mensajes

# Iniciamos la aplicación de flask
app = Flask(__name__)


@app.route("/")
def home():
    '''
    Página de inicio
    '''
    return "<h1>¡Hola!</h1>"


@app.route("/users")
def get_users():
    '''
    Obtiene todos los usuarios
    '''
    users = list(usuarios.find({}, {"_id": 0}))

    return json.jsonify(users)


@app.route("/users/<int:uid>")
def get_user(uid):
    '''
    Obtiene el usuario de id entregada
    '''
    user = list(usuarios.find({"uid": uid}, {"_id": 0}))
    if user == []:
        return json.jsonify({"success": False, 'message': f"No existe el usuario {uid}"})
    return json.jsonify(user)


@app.route("/messages/<int:mid>")
def get_message(mid):
    message = list(mensajes.find({"mid": mid}, {"_id": 0}))
    if message == []:
        return json.jsonify({"success": False, 'message': f"No existe el mensaje {mid}"})
    return json.jsonify(message)


@app.route("/messages")
def get_exchange():
    '''
    Obtiene el usuario de id entregada
    '''
    id1 = request.args.get("uid1", False)
    id2 = request.args.get("uid2", False)
    if id1 == False and id2 == False:
        messages = list(mensajes.find({}, {"_id": 0}))
        return json.jsonify(messages)
    uid1int = int(id1)
    uid2int = int(id2)
    msjs = list(mensajes.find({"sender": uid1int, "receptant": uid2int}, {"_id": 0}))
    msjs2 = list(mensajes.find({"sender": uid2int, "receptant": uid1int}, {"_id": 0}))
    msjs.extend(msjs2)
    if msjs == []:
        return json.jsonify({"success": False, 'message': f"No existen mensajes entre el usuario {uid1int} y el usuario {uid2int}"})
    return json.jsonify(msjs)


@app.route("/text-search")
def text_search():
    string = str()
    get_de_json = request.get_json()
    if get_de_json == None:
        messages = list(mensajes.find({}, {"_id": 0}))
        return json.jsonify(messages)

    dicc_json = dict(get_de_json)
    if "desired" in dicc_json:
        desired = dicc_json["desired"]
        for palabra in desired:
            string += palabra + ' '
            '''
            if len(palabra.split()) == 1:
                string += palabra + ' '
            else:
                string += '\\"' + palabra + '\\"' + ' '
            '''
    if "required" in dicc_json:
        required = dicc_json["required"]
        for palabra in required:
            if len(palabra.split()) == 1:
                string += '\"' + palabra + '\"' + ' '
            else:
                string += '\"' + palabra + '\"' + ' '
    if "forbidden" in dicc_json:
        forbidden = dicc_json["forbidden"]
        for palabra in forbidden:
            if len(palabra.split()) == 1:
                string += '-' + palabra + ' '
            else:
                string += '-\"' + palabra + '\"' + ' '
    string = string[:-1]
    if "userID" in dicc_json:
        uid = dicc_json["userID"]
    else:
        return json.jsonify({"success": False, 'message': "Error, falta id usuario"})

    print("**********************")
    print(string)
    print("**********************")
    if ("required" not in dicc_json or dicc_json["required"] == []) and ("desired" not in dicc_json or dicc_json["desired"] == []):
        print("**************entre********")
        solo_neg = list(mensajes.find({"sender": uid}, {"_id": 0}))
        final = []
        for mensaje in solo_neg:
            for prohibida in dicc_json["forbidden"]:
                if prohibida not in mensaje["message"]:
                    final.append(mensaje)
        return json.jsonify(final)
    lista = list(mensajes.find({"$text": {"$search": string}, "sender": uid}, {"_id": 0}))
    return json.jsonify(lista)



@app.route("/messages", methods=['POST'])
def create_mensajes():
    '''
    Crea un nuevo mensaje en la base de datos
    Se  necesitan todos los atributos de model, a excepcion de _id
    '''

    # verificar correctitud de atributos entregados
    keys = MENSAJES_KEYS[:]
    keys.remove('mid')
    request_json = request.get_json()

    if request_json == None:
        return json.jsonify({"success": False, 'message': "No se encontró el mensaje"})

    request_json = dict(request_json)
    total_keys = len(keys)
    keys_count = 0
    m_keys = keys[:]

    for k in request_json:
        if k in m_keys:
            keys_count += 1
            m_keys.remove(k)
        else: 
            return json.jsonify({"success": False, 'message': f'El atributo {k} no es válido'})

    if keys_count != total_keys:
        falta = ', '.join(m_keys)
        return json.jsonify({"success": False, 'message': f'Falta el/los atributo/s: {falta}'})

    # verificar existencia de users
    u1 = list(usuarios.find({"uid": request_json['sender']}, {"_id": 0}))
    if u1 == []:
        return json.jsonify({"success": False, 'message': f"No existe el sender"})
    u2 = list(usuarios.find({"uid": request_json['receptant']}, {"_id": 0}))
    if u1 == []:
        return json.jsonify({"success": False, 'message': f"No existe el receptant"})

    # verificar datos
    if not isinstance(request_json['lat'], float):
        return json.jsonify({"success": False, 'message': f"Atributo lat debe ser un número"})
    if not isinstance(request_json['long'], float):
        return json.jsonify({"success": False, 'message': f"Atributo long debe ser un número"})

    # Se inserta en la bdd
    data = {key: request_json[key] for key in keys}
    data['mid'] = len(list(mensajes.find({}, {"_id": 0}))) + 1
    # El valor de result nos puede ayudar a revisar
    # si el usuario fue insertado con éxito
    result = mensajes.insert_one(data)

    return json.jsonify({"success": True})


@app.route("/messages/<int:mid>", methods=['DELETE'])
def delete_mensaje(mid):
    '''
    Elimina el mensaje de id entregada
    '''

    #request_json = request.get_json()
    message = list(mensajes.find({"mid": mid}, {"_id": 0}))
    if message == []:
        return json.jsonify({"success": False, 'message': "No se encontró el mensaje"})

    #request_json = dict(request_json)
    #mid = request_json['mid']
    mensajes.remove({"mid": mid})
    return json.jsonify({"success": True})


if __name__ == '__main__':
    #app.run()
    app.run(debug=True)
