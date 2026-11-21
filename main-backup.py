from fastapi import FastAPI

api = FastAPI()
all_todos = [{'todo_id': 1, 'todo_name': 'sports', 'todo_description': 'palying cricket'},
             {'todo_id': 2, 'todo_name': 'read',
              'todo_description': 'read five pages'},
             {'todo_id': 3, 'todo_name': 'shop',
              'todo_description': 'shop formal clothing'},
             {'todo_id': 4, 'todo_name': 'study',
              'todo_description': 'read one hour'},
             {'todo_id': 5, 'todo_name': 'meditate', 'todo_description': 'meditate for five minutes'}]


@api.get('/toddos')
def getTodos():
    return {'result': all_todos}

# searching by parameters...


@api.get('/toddosbyid/{todo_id}')
def getToddosById(todo_id: int):
    for todo in all_todos:
        if todo['todo_id'] == todo_id:
            return {'result': todo}
        else:
            return {'result': 'no matching record'}
# get item by query string


@api.get('/getTodoByQueryString')
def getTodoByQueryString(first_n: int = None):
    for todo in all_todos:
        if first_n:
            return {'result': all_todos[:first_n]}
        else:
            return {'result': all_todos}


@api.put('/putdataTodo')
def updateTodo(todo: dict):
    last_todo = all_todos.pop()  # get last item in index-
    todo_id = last_todo['todo_id']+1
    print(todo_id)
    all_todos.append(
        {'todo_id': todo_id, 'todo_name': todo['todo_name'], 'todo_description': todo['todo_description']})
    print(all_todos)
    return {'result': todo}


@api.get('/')
def index():
    return {"message", "Hello World from Fast API Server !"}


@api.get('/calculation')
def calculation():
    pass
    return ""


@api.get('/database-operation')
def dbcall():
    return {"message", "dbcall"}
