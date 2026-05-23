from flask import jsonify


def success(data=None, message='ok', status=200):
    resp = {'code': 0, 'message': message}
    if data is not None:
        resp['data'] = data
    return jsonify(resp), status


def error(message='error', status=400, code=-1):
    return jsonify({'code': code, 'message': message}), status
