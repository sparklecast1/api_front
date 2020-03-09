#!flask/bin/python
from flask import Flask, jsonify, abort, request, make_response, url_for
from flask_httpauth import HTTPBasicAuth
from kafka import KafkaProducer
#import kafka
import os
import logging



# envoronment
#producer = KafkaProducer(bootstrap_servers=os.environ['KAFKA_SERVER'])
#topic = os.environ['KAFKA_TOPIC']
producer = KafkaProducer(bootstrap_servers='192.168.99.117:9092')
topic = "api_front"

app = Flask(__name__, static_url_path="")
#auth = HTTPBasicAuth()


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
    message = b'msg %d' % data
    future = producer.send(topic, bytes(message, encoding='utf-8'))
    record_metadata = future.get(timeout=5)



@app.errorhandler(400)
def not_found(error):
    return make_response(jsonify({'error': 'Bad request'}), 400)


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
    kafka_prodecer_send("api", task)
    print("Debug: create {}".format(task))
    return jsonify({'result': True}), 201


@app.route('/api/v1.0/tasks/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    task = filter(lambda t: t['id'] == task_id, tasks)
    if len(task) == 0:
        abort(404)
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
    kafka_prodecer_send("api", task)
    print("Debug: put {}".format(task))
    return jsonify({'result': True}), 201
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
    kafka_prodecer_send("api", task)
    print("Debug: delete {}".format(task))
    return jsonify({'result': True}), 201


if __name__ == '__main__':
    app.run(debug=True)