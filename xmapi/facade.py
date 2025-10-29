
import xmapi.entityInventory
import xmapi

_entityTypes = {}

def get_entityTypes(refresh=False):
    r = xmapi.entityInventory.entityTypes()
    if r.status_code != 200:
        return None
    
    json = r.json()

    global _entityTypes
    if refresh or not _entityTypes:
        types = {}
        for type in json["data"]:
            types[type["id"]] = type["displayName"]

        _entityTypes = types

    return _entityTypes



def get_sensors(do_post = False, page=1, pageSize=100,search=None):
    params={ 
        'page':page,
        'pageSize':pageSize,
    }

    if search:
        params['search']= f'{{"$regex":"/{search}/i"}}'

    if do_post:
        result = xmapi.api_post("sensors", params=params)
    else:
        result = xmapi.api_get("sensors", params=params)

    return result

def get_all_sensors(searchTerm = None):
    sensors = []
    page = 1
    pageSize = 100

    while True:
        result = get_sensors(search=searchTerm, page=page, pageSize=pageSize)
        if result.status_code < 200 or result.status_code > 299:
            return None

        json = result.json()

        for sensor in json['data']:
            sensors.append(sensor)

        if "nextLink" in json['paging']:
            page += 1
        else:
            return sensors