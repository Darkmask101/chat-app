from flask import Flask, render_template, redirect, url_for, session, request
from flask_socketio import join_room, leave_room, SocketIO, send
import random
from string import ascii_uppercase

app = Flask(__name__)
app.config['SECRET_KEY'] = 'abcdefchh'
socketio = SocketIO(app)

rooms = {}

def generate_code(length):
    while True:
        code = ''.join(random.choice(ascii_uppercase) for _ in range(length))
        if code not in rooms:
            return code

@app.route('/', methods=['POST', 'GET'])
def home():
    session.clear()
    if request.method == 'POST':
        name = request.form.get('name')
        code = request.form.get('code')
        join = 'join' in request.form
        create = 'create' in request.form

        if not name:
            return render_template('home.html', error='Please enter a name', code=code, name=name)

        if join and not code:
            return render_template('home.html', error='Please enter the room code', code=code, name=name)

        room = code
        if create:
            room = generate_code(4)
            rooms[room] = {"members": 0, "messages": []}
        elif code not in rooms:
            return render_template('home.html', error='Room code does not exist', code=code, name=name)

        session['name'] = name
        session['room'] = room
        return redirect(url_for('room'))

    return render_template('home.html')

@app.route('/room')
def room():
    room = session.get('room')
    name = session.get('name')
    if room is None or name is None or room not in rooms:
        return redirect(url_for('home'))

    return render_template('room.html', name=name, room=room)

@socketio.on("connect")
def connect():
    name = session.get("name")
    room = session.get("room")

    if not room or not name:
        return
    if room not in rooms:
        leave_room(room)
        return

    join_room(room)

    send({"name": name, "message": "has entered the room"}, to=room)
    rooms[room]["members"] += 1
    print(f'{name} joined the room {room}')

@socketio.on("message")
def message(data):
    room = session.get('room')
    if room not in rooms:
        return
    
    content = {
        "name": session.get("name"),
        "message": data["data"]
    }

    send(content, to=room)
    rooms[room]["messages"].append(content)
    print(f"{session.get('name')} said: {data['data']}")

@socketio.on("disconnect")
def disconnect():
    room = session.get('room')
    name = session.get('name')

    leave_room(room)

    if room in rooms:
        rooms[room]["members"] -= 1
        if rooms[room]["members"] <= 0:
            del rooms[room]

    send({"name": name, "message": "has left the room"}, to=room)
    print(f'{name} has left the room {room}')

if __name__ == '__main__':
    socketio.run(app, debug=True)
