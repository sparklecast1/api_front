#!flask/bin/python
from time import sleep
import json

from flask import Flask, jsonify, abort, request, make_response, url_for
import socket
import os
import logging



# envoronment
#kafka_proxy = os.environ['KAFKA_SERVER']
#topic = os.environ['KAFKA_TOPIC']
topic = "api_front"
KAFKA_PROXY = '192.168.99.117'
TCP_PORT = 4443
BUFFER_SIZE = 1024


app = Flask(__name__, static_url_path="")



def get_module_logger(mod_name):
    """
    To use this, do logger = get_module_logger(__name__)
    """
    logger = logging.getLogger(mod_name)
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        '%(asctime)s [%(name)-12s] %(levelname)-8s %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)
    return logger



def kafka_producer_send(MESSAGE):
    print("send data")
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((KAFKA_PROXY, TCP_PORT))
    #mess_byte = json.dumps(MESSAGE).encode('utf-8')
    s.send(json.dumps(MESSAGE).encode('utf-8'))
    #s.send(MESSAGE)
    data = s.recv(BUFFER_SIZE)
    s.close()
    print("received data:", data)
    return 1

'''
@app.errorhandler(400)
def not_found(error):
    return make_response(jsonify({'error': 'Bad request'}), 400)
'''

@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)

def make_public_task(task):
    new_task = {}
    for field in task:
        if field == 'id':
            new_task['uri'] = url_for('get_task', task_id=task['id'], _external=True)
        else:
            new_task[field] = task[field]
    return new_task


# must be routed to database directly
#--------------------------------------------------------------------
@app.route('/api/v1.0/tasks', methods=['GET'])
def get_tasks():
    return jsonify({'tasks': tasks})

#@auth.login_required
@app.route('/api/v1.0/tasks/<int:task_id>', methods=['GET'])
def get_task(task_id):
    #print(task_id)
    task = list(filter(lambda t: t['id'] == task_id, tasks))
    if len(task) == 0:
        abort(404)
    return jsonify({'task': make_public_task(task[0])})
#----------------------------------------------------------------------

@app.route('/api/v1.0/tasks', methods=['POST'])
def create_task():
    if not request.json or not 'title' in request.json:
        abort(400)
    task = {
        'task': "create",
        'title': request.json['title'],
        'description': request.json.get('description', "")
    }
    if kafka_producer_send(task):
        print("Debug: create {}".format(str(task)))
        return jsonify({'result': True}), 201
    else:
        return jsonify({'result': False}), 500


@app.route('/api/v1.0/tasks/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    #task = filter(['id'] == task_id)
    #if len(task) == 0:
    #    abort(404)
    if not request.json:
        abort(400)
    if 'title' in request.json and type(request.json['title']) != unicode:
        abort(400)
    if 'description' in request.json and type(request.json['description']) is not unicode:
        abort(400)
    if 'done' in request.json and type(request.json['done']) is not bool:
        abort(400)
    #task[0]['title'] = request.json.get('title', task[0]['title'])
    #task[0]['description'] = request.json.get('description', task[0]['description'])
    #task[0]['done'] = request.json.get('done', task[0]['done'])
    task = {
        'task': "update",
        'id': task_id,
        'title': request.json.get('title', task[0]['title']),
        'description': request.json.get('description', task[0]['description'])
    }
    kafka_producer_send(task)

    if kafka_producer_send(task):
        print("Debug: put {}".format(str(task)))
        return jsonify({'result': True}), 200
    else:
        return jsonify({'result': False}), 500
   # return jsonify({'task': make_public_task(task[0])})


@app.route('/api/v1.0/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    task = filter(lambda t: t['id'] == task_id, tasks)
    if len(task) == 0:
        abort(404)
    #tasks.remove(task[0])

    task = {
        'task': "delete",
        'id': task_id

    }
    kafka_producer_send(task)

    if kafka_producer_send(task):
        print("Debug: delete {}".format(str(task)))
        return jsonify({'result': True}), 200
    else:
        return jsonify({'result': False}), 500

@app.route('/')
def alive_task():
    return 'im alive\n'


if __name__ == '__main__':
    #app.run(debug=True, port=80, host='0.0.0.0')
    app.run(debug=True)