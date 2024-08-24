from fastapi import FastAPI, Body, status
from fastapi.responses import JSONResponse, FileResponse
import sqlite3

with sqlite3.connect("ToDo.dB") as con:
    cur = con.cursor()
    # не забыть удалить
    # табле под пользователей, данные для авторизации
    cur.execute(
        """CREATE TABLE IF NOT EXISTS Users(
                ID INTEGER PRIMARY KEY,
                Name TEXT DEFAULT "Unknown" ,
                Login TEXT NOT NULL UNIQUE ,
                Password TEXT NOT NULL
                )"""
    )
    # мб каскадное удаление не нужно будет, я не планировала кикакть пользователей, но мб добавлю
    cur.execute(
        """CREATE TABLE IF NOT EXISTS Notes(
                ID INTEGER PRIMARY KEY,
                Task TEXT NOT NULL,
                Time TEXT,
                User_ID INTEGER,
                FOREIGN KEY (User_ID) REFERENCES Users(ID) ON DELETE CASCADE 
    )"""
    )


# методы для бд, их надо вынести в методы класса?
def readBD(id_user):
    # надо отчищать чтобы данные не дублировались
    new_notes.clear()
    with sqlite3.connect("ToDo.dB") as con:
        cur = con.cursor()
        cur.execute("""SELECT * FROM Notes WHERE User_ID=?""", (id_user,))
        for result in cur:
            new_notes.append(
                {
                    "id": result[0],
                    "name": result[1],
                    "time": result[2],
                    "id_user": result[3],
                }
            )


# чтение одной записи
def readNoteBD(id):
    with sqlite3.connect("ToDo.dB") as con:
        cur = con.cursor()
        cur.execute("""SELECT * FROM Notes WHERE ID=?""", (id,))
        return cur.fetchone()


def insertBD(data):
    with sqlite3.connect("ToDo.dB") as con:
        # этой m быть не должно надо к авторизации блин уже!
        cur = con.cursor()
        if 'idUser' in globals():
            cur.execute(
                """INSERT INTO Notes(Task,Time,User_ID) VALUES(?, ?, ?) """,
                (data["name"], data["time"], idUser),
            )
        else:
            cur.execute(
                """INSERT INTO Notes(Task,Time,User_ID) VALUES(?, ?, ?) """,
                (data["name"], data["time"], 1),
            )
        # исправить на возвращение из боди именно User_ID, но пока там такого нет и так сойдет
        return cur.lastrowid


def updateBD(data):
    with sqlite3.connect("ToDo.dB") as con:
        cur = con.cursor()
        cur.execute(
            """UPDATE Notes SET Task =?, Time=? WHERE ID=?""",
            (data["name"], data["time"], data["id"]),
        )


def deleteDB(id):
    with sqlite3.connect("ToDo.dB") as con:
        cur = con.cursor()
        cur.execute("""DELETE FROM Notes  WHERE ID=?""", (id,))


def selectUser(data):
    with sqlite3.connect("ToDo.dB") as con:
        cur = con.cursor()
        cur.execute(
            """SELECT * FROM Users WHERE Login=? AND Password=?""",
            (data["login"], data["password"]),
        )
        return cur.fetchone()

def insertUser(data):
    with sqlite3.connect("ToDo.dB") as con:
        cur = con.cursor()
        cur.execute(
            """INSERT INTO Users(Name,Login,Password) VALUES(?, ?, ?) """,(data["name"], data["login"], data["password"]),
        )
        return cur.lastrowid

new_notes = []
# 1 юзер это просто заглушка, чтобы можно было создавать заметки и без авторизации.да их все будут видеть ну и что
# idUser=1
app = FastAPI()


# база
@app.get("/")
async def main():
    return FileResponse("public/index.html")


@app.get("/api/notes")
def get_notes():
    # надо брать ID пользователя который зашел на страницу, получается надо в боди передавать как раз айдишник, но юра сказал не через боди делать, но как...
    if 'idUser' in globals():
        readBD(idUser)
    else:
        readBD(1)
    print("-------")
    #print(idUser)
    print(new_notes)
    print("-------")
    return new_notes


@app.get("/api/notes/{id}")
def get_note(id: int):
    note = readNoteBD(id)
    if note is None:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"message": "Такой заметки нет"},
        )
    return {"id": note[0], "name": note[1], "time": note[2], "id_user": note[3]}


# вывести в клаасы файлы.получается надо работу с сохранением считыванием дж вынести в класс и у него обращаться к методам класса?
@app.post("/api/notes")
def create_note(data=Body()):
    note_id = insertBD(data)
    note = readNoteBD(note_id)
    new_notes.append(
        {"id": note[0], "name": note[1], "time": note[2], "id_user": note[3]}
    )
    # мб поменять на {"name": note[1], "time": note[2],}
    return {"id": note[0], "name": note[1], "time": note[2], "id_user": note[3]}


# редактирование заметок. а оно блин вообще надо??..
@app.put("/api/notes")
def edit_note(data=Body()):
    note = readNoteBD(data["id"])
    if note is None:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"message": "Такой заметки нет"},
        )

    updateBD(data)
    updated_note = readNoteBD(data["id"])
    if updated_note:
        return {
            "id": updated_note[0],
            "name": updated_note[1],
            "time": updated_note[2],
            "id_user": updated_note[3],
        }
    else:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"message": "Заметка не обновлена"},
        )


# удаление заметок
@app.delete("/api/notes/{id}")
def delete_note(id: int):
    note = readNoteBD(id)
    print(note)
    if note == None:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"message": "Такой заметки нет"},
        )
    deleteDB(id)
    for nots in new_notes:
        if nots["id"] == id:
            new_notes.remove(nots)
            break
    return {"id": note[0], "name": note[1], "time": note[2], "id_user": note[3]}


# авторизация. 2 функци гет и пост
@app.post("/api/user")
def check_user(data=Body()):
    global idUser
    if data["login"] and data["password"]:
        user = selectUser(data)
        if user:
            # запоминается id юзера чьи заметки!!!!
            idUser = user[0]
            print(idUser)
            readBD(idUser)
            print(new_notes)
            return user[1]
        else:
            return False
    else:
        return None
    
@app.post("/api/newuser")
def new_user(data=Body()):
    idUser=insertUser(data)
    
