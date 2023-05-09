import os
import json
from flask import session
from flask_socketio import emit, join_room
from app import app, socketio, docker_client, users

def make_tree(trees:list, uuid:str):
    nodes   = []
    for tree in trees:
        if tree['type'] == 'report':
            continue
    
        node = {'text':tree['name'],'type':tree['type']}

        if tree['name'] == '.':
            node['id'] = uuid
            node['text'] = uuid
            node['state'] = {'opened':True,'selected':True}

        if tree['type'] == 'directory':
            node['children'] = make_tree(trees=tree['contents'], uuid=None)
        nodes.append(node)
    return nodes

@socketio.on(message="join", namespace="/ide/sock/")
def sock_join(message):
    """"""
    if 'uuid' not in session.keys():
        emit('redirect', {'url': f'/ide/'})
    else:
        uuid = session['uuid']
        if 'container' not in users[uuid]:
            emit('redirect', {'url': f'/ide/'})
        else:
            join_room(room=uuid)
            container_id    = users[uuid]['container']
            exec_obj        = docker_client.exec_create(container=container_id, cmd='tree -J', user='root')
            output          = docker_client.exec_start(exec_id=exec_obj['Id'])
            resp            = docker_client.exec_inspect(exec_id=exec_obj['Id'])
            exit_code       = resp['ExitCode']

            app.logger.error(f'[join] exit_code : {exit_code}, output : {output}')

            trees           = json.loads(s=output.decode())
            res             = make_tree(trees=trees, uuid=uuid)

            app.logger.error(f'[join] exit_code : {exit_code}, output : {output}')
            emit('join', {'exit_code':exit_code, 'output': f'{json.dumps(res)}'}, room=uuid)

@socketio.on(message="content", namespace="/ide/sock/")
def sock_content(message):
    """"""
    if 'uuid' not in session.keys():
        emit('redirect', {'url': f'/ide/'})
    else:
        uuid = session['uuid']
        if 'container' not in users[uuid]:
            emit('redirect', {'url': f'/ide/'})
        else:
            container_id    = users[uuid]['container']
            id              = message['id']
            file            = message['file']
            path            = os.path.join(*message['path'])

            target_path     = os.path.join('/tmp', path, file)
            cmd             = f'cat "{target_path}"'

            exec_obj        = docker_client.exec_create(container=container_id, cmd=cmd, user='root')
            output          = docker_client.exec_start(exec_id=exec_obj['Id'])
            resp            = docker_client.exec_inspect(exec_id=exec_obj['Id'])
            exit_code       = resp['ExitCode']

            app.logger.error(f'[content] exit_code : {exit_code}, output : {output}')
            emit('content', {'id':id, 'exit_code':exit_code, 'output': f'{output.decode()}'}, room=uuid)

@socketio.on(message="create", namespace="/ide/sock/")
def sock_create(message):
    """"""
    if 'uuid' not in session.keys():
        emit('redirect', {'url': f'/ide/'})
    else:
        uuid = session['uuid']
        if 'container' not in users[uuid]:
            emit('redirect', {'url': f'/ide/'})
        else:
            container_id    = users[uuid]['container']
            id              = message['id']
            file            = message['file']
            type            = message['type']
            path            = os.path.join(*message['path'])

            target_path     = os.path.join('/tmp', path, file)
            if type == 'directory':
                cmd             = f'mkdir "{target_path}"'
            else:
                cmd             = f'touch "{target_path}"'
            
            exec_obj        = docker_client.exec_create(container=container_id, cmd=cmd, user='root')
            output          = docker_client.exec_start(exec_id=exec_obj['Id'])
            resp            = docker_client.exec_inspect(exec_id=exec_obj['Id'])
            exit_code       = resp['ExitCode']

            app.logger.error(f'[create] exit_code : {exit_code}, output : {output}')
            emit('create', {'id':id, 'exit_code':exit_code, 'output':output.decode()}, room=uuid)

@socketio.on(message="rename", namespace="/ide/sock/")
def sock_rename(message):
    """"""
    if 'uuid' not in session.keys():
        emit('redirect', {'url': f'/ide/'})
    else:
        uuid = session['uuid']
        if 'container' not in users[uuid]:
            emit('redirect', {'url': f'/ide/'})
        else:
            container_id    = users[uuid]['container']
            id              = message['id']
            old             = message['file'][0]
            new             = message['file'][1]
            path            = os.path.join(*message['path'])

            old_path        = os.path.join('/tmp', path, old)
            new_path        = os.path.join('/tmp', path, new)
            cmd             = f'mv "{old_path}" "{new_path}"'
            
            exec_obj        = docker_client.exec_create(container=container_id, cmd=cmd, user='root')
            output          = docker_client.exec_start(exec_id=exec_obj['Id'])
            resp            = docker_client.exec_inspect(exec_id=exec_obj['Id'])
            exit_code       = resp['ExitCode']
            
            app.logger.error(f'[rename] exit_code : {exit_code}, output : {output}')
            emit('rename', {'id':id, 'exit_code':exit_code, 'output':output.decode(), 'old':old}, room=uuid)

@socketio.on(message="delete", namespace="/ide/sock/")
def sock_delete(message):
    """"""
    if 'uuid' not in session.keys():
        emit('redirect', {'url': f'/ide/'})
    else:
        uuid = session['uuid']
        if 'container' not in users[uuid]:
            emit('redirect', {'url': f'/ide/'})
        else:
            container_id    = users[uuid]['container']
            id              = message['id']
            file            = message['file']
            path            = os.path.join(*message['path'])

            target_path     = os.path.join('/tmp', path, file)
            cmd             = f'rm -rf "{target_path}"'
            
            exec_obj        = docker_client.exec_create(container=container_id, cmd=cmd, user='root')
            output          = docker_client.exec_start(exec_id=exec_obj['Id'])
            resp            = docker_client.exec_inspect(exec_id=exec_obj['Id'])
            exit_code       = resp['ExitCode']

            app.logger.error(f'[delete] exit_code : {exit_code}, output : {output}')
            emit('delete', {'id':id, 'exit_code':exit_code, 'output':output.decode()}, room=uuid)

@socketio.on(message="move", namespace="/ide/sock/")
def sock_move(message):
    """"""
    if 'uuid' not in session.keys():
        emit('redirect', {'url': f'/ide/'})
    else:
        uuid = session['uuid']
        if 'container' not in users[uuid]:
            emit('redirect', {'url': f'/ide/'})
        else:
            container_id    = users[uuid]['container']
            id              = message['id']
            file            = message['file']
            old_path        = os.path.join(*message['path'][0])
            new_path        = os.path.join(*message['path'][1])

            old_path        = os.path.join('/tmp', old_path, file)
            new_path        = os.path.join('/tmp', new_path, file)
            cmd             = f'mv "{old_path}" "{new_path}"'
            
            exec_obj        = docker_client.exec_create(container=container_id, cmd=cmd, user='root')
            output          = docker_client.exec_start(exec_id=exec_obj['Id'])
            resp            = docker_client.exec_inspect(exec_id=exec_obj['Id'])
            exit_code       = resp['ExitCode']

            app.logger.error(f'[delete] exit_code : {exit_code}, output : {output}')
            emit('delete', {'id':id, 'exit_code':exit_code, 'output':output.decode()}, room=uuid)

@socketio.on(message="save", namespace="/ide/sock/")
def sock_save(message):
    """"""
    if 'uuid' not in session.keys():
        emit('redirect', {'url': f'/ide/'})
    else:
        uuid = session['uuid']
        if 'container' not in users[uuid]:
            emit('redirect', {'url': f'/ide/'})
        else:
            container_id    = users[uuid]['container']
            id              = message['id']
            file            = message['file']
            path            = os.path.join(*message['path'])
            code            = message['code']
            target_path     = os.path.join('/tmp', path, file)

            with open(file=target_path, mode='w') as fp:
                fp.write(code)

            emit('save', {'id':id, 'exit_code':0, 'output':''}, room=uuid)

@socketio.on(message="run", namespace="/ide/sock/")
def sock_run(message):
    """"""
    if 'uuid' not in session.keys():
        emit('redirect', {'url': f'/ide/'})
    else:
        uuid = session['uuid']
        if 'container' not in users[uuid]:
            emit('redirect', {'url': f'/ide/'})
        else:
            container_id    = users[uuid]['container']
            uuid            = session['uuid']
            id              = message['id']
            file            = message['file']
            path            = os.path.join(*message['path'])

            target_path     = os.path.join('/tmp', path, file)
            cmd             = f'python3 -u "{target_path}"'

            exec_obj        = docker_client.exec_create(container=container_id, stdout=True, stderr=True, stdin=True, tty=True, cmd=cmd, user='root')
            output          = docker_client.exec_start(exec_id=exec_obj['Id'], detach=False, tty=True, stream=True, socket=True)
            socket          = output._sock
            users[uuid]['socket'] = socket
            while True:
                msg = socket.recv(1024)
                if not msg:
                    break
                app.logger.error(f'[run] output : {msg.decode()}')
                emit("run", {'id':id, 'exit_code':1, "output":msg.decode()}, room=uuid)
            socket.close()
            app.logger.error(f'[run] output : end')
            emit("run", {'id':id, 'exit_code':0, "output":msg.decode()}, room=uuid)

@socketio.on(message="stop", namespace="/ide/sock/")
def python_stop_code(message):
    """"""
    if 'uuid' not in session.keys():
        emit('redirect', {'url': f'/ide/'})
    else:
        uuid = session['uuid']
        if 'container' not in users[uuid]:
            emit('redirect', {'url': f'/ide/'})
        else:
            container_id    = users[uuid]['container']
            try:
                docker_client.stop(container=container_id, timeout=0)
            except Exception as e:
                app.logger.error(f'container stop : {e}')
                pass

            app.logger.error(f'[stop] output : stop')
            docker_client.start(container=container_id)

@socketio.on(message="command", namespace="/ide/sock/")
def python_command(message):
    """"""
    if 'uuid' not in session.keys():
        emit('redirect', {'url': f'/ide/'})
    else:
        uuid = session['uuid']
        if 'container' not in users[uuid]:
            emit('redirect', {'url': f'/ide/'})
        else:
            container_id    = users[uuid]['container']
            command         = message['command']
            command         = f'{command}\n'
            if 'socket' in users[uuid].keys():
                app.logger.warn(f"[stop] command : {command.encode()}")
                users[uuid]['socket']._sock.sendall(command.encode())

@socketio.on(message="terminal", namespace="/ide/sock/")
def python_terminal(message):
    """"""
    if 'uuid' not in session.keys():
        emit('redirect', {'url': f'/ide/'})
    else:
        uuid = session['uuid']
        if 'container' not in users[uuid]:
            emit('redirect', {'url': f'/ide/'})
        else:
            container_id    = users[uuid]['container']
            cmd             = f'python3 -u'

            exec_obj        = docker_client.exec_create(container=container_id, stdout=True, stderr=True, stdin=True, tty=True, cmd=cmd, user='root')
            output          = docker_client.exec_start(exec_id=exec_obj['Id'], detach=False, tty=True, stream=True, socket=True)
            socket          = output._sock
            users[uuid]['socket'] = socket
            while True:
                msg = socket.recv(1024)
                if not msg:
                    break
                app.logger.error(f'[run] output : {msg}')
                emit("run", {'exit_code':1, "output":msg.decode()}, room=uuid)
            socket.close()
            app.logger.error(f'[run] output : end')
            emit("run", {'exit_code':0, "output":msg.decode()}, room=uuid)