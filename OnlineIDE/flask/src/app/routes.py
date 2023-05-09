import os
import shutil
from uuid import uuid1
from flask import session, render_template, redirect
from app import app, users, docker_client
from .ide import python

static_config = {
    'python' : {
        'image':'python:3.8',
        'command': 'python3 -u {}',
        'terminal': 'python3 -u'
    },
}

@app.route(rule="/ide/", methods=["GET"])
def ide_main():
    return redirect('/ide/python')

@app.route(rule="/ide/<string:language>/", methods=["GET"])
def get_session(language:str):
    if 'uuid' in session.keys():
        # 이미 세션이 존재하면
        if session['uuid'] in users:
            uuid = session['uuid']

            try:
                # 기존 컨테이너 사용
                if 'container' in users[uuid].keys():
                    return redirect(f'/ide/{language}/{uuid}')
            except Exception as e:
                # 컨테이너 없음
                pass

            # 세션에 소켓이 존재하면
            if 'socket' in users[uuid].keys():
                # 소켓 삭제
                del users[uuid]['socket']
            temp_dir    = os.path.join('/tmp', uuid)
            # 임시 디렉토리가 존재하면
            if os.path.exists(path=temp_dir):
                # 임시 디렉토리 삭제
                shutil.rmtree(path=temp_dir)
            # 세션 삭제
            del users[uuid]
        session.clear()

    # 새로운 세션 아이디 발급
    uuid            = str(uuid1())
    session['uuid'] = uuid
    users[uuid]     = {}
    return redirect(f'/ide/{language}/{uuid}')

@app.route(rule="/ide/<string:language>/<string:uuid>", methods=["GET"])
def get_ide(language:str, uuid:str):
    if 'uuid' not in session.keys():
        return redirect('/ide/')
    
    uuid        = session['uuid']

    try:
        # 기존 컨테이너 사용
        if 'container' in users[uuid].keys():
            container_id    = users[uuid]['container']
            inspect         = docker_client.inspect_container(container=container_id)
            app.logger.error(f'inspect : {inspect["State"]["Status"]}')
            if inspect['State']['Status'] == 'running':
                return render_template(f"{language}.html")
            else:
                docker_client.stop(container=container_id)
                docker_client.remove_container(container=container_id, force=True)
    except Exception as e:
        # 컨테이너 없음
        app.logger.error(f'e : {e}')
        pass

    # /tmp에 사용자 디렉토리 생성
    user_path   = os.path.join('/tmp', uuid)
    if not os.path.exists(path=user_path):
        os.makedirs(name=user_path, exist_ok=True)

    # 기본 파일 생성
    default_file= 'main.py'
    default_code= '# Write Python 3 code in this editor and run it.\r\n\r\ndef greeting():\r\n    print("Hello")\r\n    print("World!")\r\n\r\ngreeting()'
    with open(file=os.path.join(user_path, default_file), mode='w') as fp:
        fp.write(default_code)

    # 컨테이너 생성
    config = {
        'hostname':'repl',
        'name':uuid,
        'stdin_open':True,
        'tty':True,
        'user':'root:root',
        'volumes': [f'{user_path}:{user_path}'],
        'host_config': docker_client.create_host_config(binds=[f'{user_path}:{user_path}:rw']),
        'working_dir':f'{user_path}',
    }
    config['image']             = static_config[language]['image']
    container                   = docker_client.create_container(**config)
    container_id                = container.get('Id')
    users[uuid]['container']    = container_id
    
    # 컨테이너 실행
    docker_client.start(container=container_id)
    app.logger.error(f'created : {container_id} by : {uuid}')
    return render_template(f"{language}.html")