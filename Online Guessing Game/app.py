from flask import Flask, render_template, request, redirect, jsonify
import random
import string
from datetime import datetime

app = Flask(__name__)

rooms = {}


def create_room_code():
    characters = string.ascii_uppercase + string.digits

    while True:
        code = "".join(random.choice(characters) for _ in range(6))

        if code not in rooms:
            return code


# =========================
# HOME
# =========================

@app.route("/", methods=["GET", "POST"])
def home():

    if request.method == "POST":

        player_name = request.form.get(
            "player_name", ""
        ).strip()

        if not player_name:
            player_name = "Player 1"

        room_code = create_room_code()

        rooms[room_code] = {
            "players": [player_name],
            "secret": random.randint(1, 100),
            "guesses": [],
            "winner": None,
            "turn": 0,
            "messages": []
        }

        return redirect(
            f"/game/{room_code}?player={player_name}"
        )

    return render_template("index.html")


# =========================
# JOIN ROOM
# =========================

@app.route("/join", methods=["POST"])
def join():

    player_name = request.form.get(
        "player_name", ""
    ).strip()

    room_code = request.form.get(
        "room_code", ""
    ).strip().upper()

    if not player_name:
        player_name = "Player 2"

    if room_code not in rooms:
        return render_template(
            "index.html",
            message="❌ Room nahi mila!"
        )

    if len(rooms[room_code]["players"]) >= 2:
        return render_template(
            "index.html",
            message="⚠️ Room already full hai!"
        )

    rooms[room_code]["players"].append(player_name)

    return redirect(
        f"/game/{room_code}?player={player_name}"
    )


# =========================
# GAME PAGE
# =========================

@app.route("/game/<room_code>")
def game(room_code):

    if room_code not in rooms:
        return "❌ Room nahi mila!"

    player_name = request.args.get(
        "player",
        "Player"
    )

    room = rooms[room_code]

    current_player = None

    if (
        len(room["players"]) == 2
        and room["winner"] is None
    ):
        current_player = room["players"][room["turn"]]

    return render_template(
        "game.html",
        room_code=room_code,
        player_name=player_name,
        players=room["players"],
        winner=room["winner"],
        guesses=room["guesses"],
        current_player=current_player,
        messages=room["messages"]
    )


# =========================
# LIVE STATUS
# =========================

@app.route("/status/<room_code>")
def status(room_code):

    if room_code not in rooms:
        return jsonify({
            "error": "Room nahi mila!"
        })

    room = rooms[room_code]

    current_player = None

    if (
        len(room["players"]) == 2
        and room["winner"] is None
    ):
        current_player = room["players"][room["turn"]]

    return jsonify({
        "players": room["players"],
        "winner": room["winner"],
        "current_player": current_player,
        "guesses": room["guesses"],
        "messages": room["messages"]
    })


# =========================
# GUESS
# =========================

@app.route("/guess/<room_code>", methods=["POST"])
def guess(room_code):

    if room_code not in rooms:
        return "❌ Room nahi mila!"

    player_name = request.form.get(
        "player_name",
        ""
    )

    guess_text = request.form.get(
        "guess",
        ""
    )

    room = rooms[room_code]

    if room["winner"] is not None:
        return redirect(
            f"/game/{room_code}?player={player_name}"
        )

    if len(room["players"]) < 2:
        return redirect(
            f"/game/{room_code}?player={player_name}"
        )

    current_player = room["players"][room["turn"]]

    if player_name != current_player:
        return redirect(
            f"/game/{room_code}?player={player_name}"
        )

    try:
        number = int(guess_text)
    except ValueError:
        return redirect(
            f"/game/{room_code}?player={player_name}"
        )

    if number < 1 or number > 100:
        return redirect(
            f"/game/{room_code}?player={player_name}"
        )

    secret = room["secret"]

    if number == secret:

        result = "🎯 CORRECT! Secret number mil gaya!"

        room["winner"] = player_name

    elif number < secret:

        result = "📈 Secret number BADA hai."

    else:

        result = "📉 Secret number CHHOTA hai."

    room["guesses"].append({
        "player": player_name,
        "number": number,
        "result": result
    })

    if room["winner"] is None:

        if room["turn"] == 0:
            room["turn"] = 1
        else:
            room["turn"] = 0

    return redirect(
        f"/game/{room_code}?player={player_name}"
    )


# =========================
# SEND CHAT MESSAGE
# =========================

@app.route("/chat/<room_code>", methods=["POST"])
def chat(room_code):

    if room_code not in rooms:
        return jsonify({
            "success": False,
            "message": "Room nahi mila!"
        })

    player_name = request.form.get(
        "player_name",
        ""
    ).strip()

    message = request.form.get(
        "message",
        ""
    ).strip()

    # Empty message ignore
    if not message:
        return jsonify({
            "success": False
        })

    # Message length limit
    if len(message) > 200:
        message = message[:200]

    room = rooms[room_code]

    # Sirf room ke players message bhej sakte hain
    if player_name not in room["players"]:
        return jsonify({
            "success": False
        })

    current_time = datetime.now().strftime("%H:%M")

    room["messages"].append({
        "player": player_name,
        "message": message,
        "time": current_time
    })

    # Bahut purane messages remove
    if len(room["messages"]) > 100:
        room["messages"] = room["messages"][-100:]

    return jsonify({
        "success": True
    })


# =========================
# START SERVER
# =========================

if __name__ == "__main__":
    app.run(debug=True)