import json
import random
import requests
from flask import Flask, jsonify, request

app = Flask(__name__)

titleider = "YOUR_TITLEIDER"
secretkey = "YOUR_SECRET_KEY"
ApiKey = "YOUR_API_KEY"
def GetAuthHeaders() -> dict:
    return {"Content-Type": "application/json", "X-SecretKey": secretkey}

@app.route("/api/PlayFabAuthentication", methods=["POST"])
def playfab_authentication():
    login_req = requests.post(
        url=f"https://{titleider}.playfabapi.com/Server/LoginWithServerCustomId",
        json={"ServerCustomId": "OCULUS" + request.json.get('oculus_id', ''), "CreateAccount": True},
        headers=GetAuthHeaders()
    )

    if login_req.status_code == 200:
        rjson = login_req.json()
        session_ticket = rjson.get('data').get('SessionTicket')
        entity_token = rjson.get('data').get('EntityToken').get('EntityToken')
        playfab_id = rjson.get('data').get('PlayFabId')
        entity_id = rjson.get('data').get('EntityToken').get('Entity').get('Id')
        entity_type = rjson.get('data').get('EntityToken').get('Entity').get('Type')

        try:
            requests.post(
                f"https://{titleider}.playfabapi.com/Client/LinkCustomID",
                json={"CustomId": request.json.get('oculus_id', ''), "ForceLink": True},
                headers={"Content-Type": "application/json", "X-Authorization": session_ticket}
            )
        except requests.exceptions.RequestException as e:
            app.logger.error(f"Failed to link Oculus ID {request.json.get('oculus_id', '')} for PlayFabId {playfab_id}: {str(e)}")

        return jsonify({
            "SessionTicket": session_ticket,
            "EntityToken": entity_token,
            "PlayFabId": playfab_id,
            "EntityId": entity_id,
            "EntityType": entity_type
        }), 200
    else: 
        ban_info = login_req.json()
        if ban_info.get("errorCode") == 1002:
            ban_message = ban_info.get("errorMessage", "No ban message provided.")
            ban_details = ban_info.get("errorDetails", {})
            ban_expiration_key = next(iter(ban_details.keys()), None)
            ban_expiration_list = ban_details.get(ban_expiration_key, [])
            ban_expiration = (
                ban_expiration_list[0]
                if len(ban_expiration_list) > 0
                else "Indefinite"
            )

            return jsonify({
                "BanMessage": ban_expiration_key,
                "BanExpirationTime": ban_expiration,
            }), 403     

@app.route("/api/CachePlayFabId", methods=["POST"])
def cacheplayfabid():
    idfk = request.get_json()
    playfabid = idfk.get("SessionTicket").split("-")[0] if "SessionTicket" in idfk else None
    if playfabid is None:
        return jsonify({"Message": "Try Again Later."}), 404
    return jsonify({"Message": "Authed", "PlayFabId": playfabid}), 200

@app.route("/", methods=["POST", "GET"])
def Rizz():
    return "ken him"

@app.route("/api/TitleData", methods=["POST", "GET"])
def title_data():
    response = requests.post(
        url=f"https://{titleider}.playfabapi.com/Server/GetTitleData",
        headers=settings.get_auth_headers()
    )

    if response.status_code == 200:
        return jsonify(response.json().get("data").get("Data"))
    else:
        return jsonify({}), response.status_code


@app.route("/api/ConsumeOculusIAP", methods=["POST"])
def consume_oculus_iap():
    rjson = request.get_json()
    access_token = rjson.get("userToken")
    user_id = rjson.get("userID")
    nonce = rjson.get("nonce")
    sku = rjson.get("sku")

    response = requests.post(
        url=f"https://graph.oculus.com/consume_entitlement?nonce={nonce}&user_id={user_id}&sku={sku}&access_token={ApiKey}",
        headers={"content-type": "application/json"}
    )

    if response.json().get("success"):
        return jsonify({"result": True})
    else:
        return jsonify({"error": True})

@app.route("/api/photon", methods=["POST"])
def photonauth():
    print(f"Received {request.method} request at /api/photon")
    getjson = request.get_json()
    Ticket = getjson.get("Ticket")
    Nonce = getjson.get("Nonce")
    Platform = getjson.get("Platform")
    if Ticket is None or len(Ticket.split('-')[0]) != 16:
        return jsonify({'resultCode': 2, 'message': 'Invalid token', 'userId': None, 'nickname': None}), 403
        
    req = requests.post(
        url=f"https://{titleider}.playfabapi.com/Server/GetUserAccountInfo",
        json={"PlayFabId": Ticket.split('-')[0]},
        headers={"content-type": "application/json", "X-SecretKey": secretkey}
    )

    if req.status_code == 200:
        nickName = req.json().get("UserInfo", {}).get("UserAccountInfo", {}).get("Username")
        return jsonify({
            'resultCode': 1,
            'message': 'Authenticated',
            'userId': Ticket.split('-')[0],
            'nickname': nickName
        })
    else:
        return jsonify({"resultCode": 0, "message": "Something went wrong"}), 500

if __name__ == "__main__":
    app.run(debug=True)
