#!flask/bin/python
from time import sleep
import json

from flask import Flask, jsonify, abort, request, make_response, url_for
from kafka import KafkaProducer
from kafka.errors import KafkaError
#import kafka
import os
import logging



# envoronment
#producer = KafkaProducer(bootstrap_servers=os.environ['KAFKA_SERVER'])
#topic = os.environ['KAFKA_TOPIC']
producer = KafkaProducer(bootstrap_servers='192.168.99.117:9092',
                         value_serializer=lambda x:
                         json.dumps(x).encode('utf-8'))
topic = 'api_front'



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



def kafka_prodecer_send(to_topic, data):
    print("Kafka send data")
    future = producer.send(to_topic, value=data)
    try:
        record_metadata = future.get(timeout=5)
        return 1
    except KafkaError:
        #log.exception()
        print("Warn: error timeout")
        pass
    return 0



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
    if kafka_prodecer_send(topic, task):
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
    kafka_prodecer_send(topic, task)

    if kafka_prodecer_send(topic, task):
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
    kafka_prodecer_send(topic, task)

    if kafka_prodecer_send(topic, task):
        print("Debug: delete {}".format(str(task)))
        return jsonify({'result': True}), 200
    else:
        return jsonify({'result': False}), 500

@app.route('/')
def alive_task():
    return 'im alive\n'


if __name__ == '__main__':
    app.run(debug=True, port=80, host='0.0.0.0')
    #app.run(debug=True)