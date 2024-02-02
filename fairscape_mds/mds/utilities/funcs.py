from fastapi.responses import JSONResponse
import json
import requests


def parse_request(req):
    success, inputs = gather_inputs(req)

    if not success:
        return False, '', '', 'POST json with keys datasetID and scriptID'
    try:
        data_id = inputs[DATASET_KEY]
    except:
        return False, '', '', 'Missing required key datasetID'

    try:
        script_id = inputs[SCRIPT_KEY]
    except:
        return False, '', '', 'Missing required key scriptID'

    return True, data_id, script_id, ''


def gather_inputs(req):
    if req == b'':
        return False, JSONResponse(
            {'error': "Invalid input data: expecting jobID, datasetID, scriptID", 'valid': False})

    try:
        inputs = json.loads(req)
    except:
        return False, JSONResponse({'error': "Invalid JSON file", 'valid': False})

    return True, inputs


def get_dist_ids(id):
    if isinstance(id, list):
        dist_ids = []
        file_names = []
        for i in id:
            if i == '':
                continue
            current_id, file_name = get_dist_ids(i)
            dist_ids.append(current_id)
            file_names.append(file_name)
        return dist_ids, file_names

    r = requests.get(ROOT_URL + id)

    data_dict = r.json()
    if isinstance(data_dict['distribution'], list):
        if data_dict['distribution'][-1].get('@type', '') == 'DataDownload':
            data_url = data_dict['distribution'][-1]['contentUrl']
            file_name = data_url.split('/')[-1]
            dist_id = data_dict['distribution'][-1]['@id']
        else:
            dist_r = requests.get(ROOT_URL + data_dict['distribution'][-1]['@id'])
            data_url = dist_r.json()['name']
            file_name = data_url.split('/')[-1]
            dist_id = data_dict['distribution'][-1]['@id']
    elif isinstance(data_dict['distribution'], dict):
        if data_dict['distribution'].get('@type', '') == 'DataDownload':
            data_url = data_dict['distribution']['contentUrl']
            file_name = data_url.split('/')[-1]
            dist_id = data_dict['distribution']['@id']
        else:
            dist_r = requests.get(ROOT_URL + data_dict['distribution']['@id'])
            data_url = dist_r.json()['name']
            file_name = data_url.split('/')[-1]
            dist_id = data_dict['distribution']['@id']
    else:
        dist_r = requests.get(ROOT_URL + data_dict['distribution'])
        data_url = dist_r.json()['name']
        file_name = data_url.split('/')[-1]
        dist_id = data_dict['distribution']
    return dist_id, file_name


def get_distribution_attr(resouce_id, resource):
    try:
        data_dict = resource.json()
        if isinstance(data_dict['distribution'], list):
            if data_dict['distribution'][-1].get('@type', '') == 'DataDownload':
                download_id = data_dict['distribution'][-1]['@id']
                file_location = data_dict['distribution'][-1]['contentUrl']
                file_name = '/'.join(file_location.split('/')[1:])

        else:
            if data_dict['distribution'].get('@type', '') == 'DataDownload':
                download_id = data_dict['distribution']['@id']
                file_location = data_dict['distribution']['contentUrl']
                file_name = '/'.join(file_location.split('/')[1:])
    except:
        return '', '', ''

    return download_id, file_location, file_name


def to_str(bytes_or_str):
    if isinstance(bytes_or_str, bytes):
        value = bytes_or_str.decode('utf-8')
    else:
        value = bytes_or_str
    return value  # Instance of str
