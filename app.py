from flask import Flask, redirect, render_template, url_for
from flask_socketio import SocketIO, emit

app = Flask(__name__)
socketio = SocketIO(app)

players = []
pot = 0

# 使用字典来存储每个玩家的唯一标识符、初始钱数和当前钱数
player_data = {}


@app.route("/")
def index():
    return redirect(url_for("join"))


@app.route("/join")
def join():
    return render_template("join.html")


@app.route("/clean")
def clean():
    global players
    global pot
    global player_data
    players = []
    pot = 0
    player_data = {}
    return redirect(url_for("join"))


@app.route("/game")
def game():
    return render_template("index.html")


@socketio.on("connect")
def handle_connect():
    print("Client connected")
    emit("update", {"pot": pot})
    emit("update_players", {"players": get_players_with_money()}, broadcast=True)


@socketio.on("disconnect")
def handle_disconnect():
    print("Client disconnected")


@socketio.on("join")
def handle_join(data):
    player = data["player"]
    if player not in player_data:
        players.append(player)
        player_data[player] = {"initial_money": 1000, "money": 1000, "bet_amount": 0}
        emit("update_players", {"players": get_players_with_money()}, broadcast=True)
        emit("update_money", {"money": player_data[player]["money"]})


@socketio.on("bet")
def handle_bet(data):
    global pot
    player = data["player"]
    bet_amount = data["bet"]
    pot += bet_amount
    player_data[player]["money"] -= bet_amount
    player_data[player]["bet_amount"] += bet_amount
    emit("update", {"pot": pot}, broadcast=True)
    emit("update_players", {"players": get_players_with_money()}, broadcast=True)
    emit("update_money", {"money": player_data[player]["money"]})


@socketio.on("settle")
def handle_settle(data):
    global pot
    winner = data["winner"]
    player_data[winner]["money"] += pot
    emit("update_players", {"players": get_players_with_money()}, broadcast=True)
    emit("settle_message", {"message": f"{winner} wins ${pot}!"}, broadcast=True)
    pot = 0
    reset_bet_amount()
    emit("update", {"pot": pot}, broadcast=True)
    emit("update_money", {"money": player_data[winner]["money"]})
    emit("update_players", {"players": get_players_with_money()}, broadcast=True)


def get_players_with_money():
    return [
        {
            "name": player,
            "money": player_data[player]["money"],
            "bet_amount": player_data[player]["bet_amount"],
        }
        for player in players
    ]


def reset_bet_amount():
    for player in players:
        player_data[player]["bet_amount"] = 0


if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=80)
