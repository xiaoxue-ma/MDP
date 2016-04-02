import json


def android_to_algo(msg):
    if (msg == "explore"):
        return "SE"
    elif (msg == "endexplore"):
        return "EE"
    elif (msg == "run"):
        return "SF"
    elif (msg == "endrun"):
        return "EF"
    else:
        return "SE"


def algo_to_android(msg):
    if msg == "SE":
        return json.dumps({"type":"stc","msg":"explore"})
    elif msg == "EE":
        return json.dumps({"type":"cmd","msg":"endexplore"})
    elif len(msg) > 10:
        return json.dumps({"type":"ums","msg":msg})
    else:
        return json.dumps({"type":"ur","msg":msg})


def arduino_to_algo(msg):
    if (msg == '0'):
        return "M"
    elif (msg == '1'):
        return "R"
    elif (msg == '2'):
        return "L"
    elif (msg == '3'):
        return "B"
    elif msg == '4':
        return "SE"
    elif msg == '5':
        return "SF"
    elif msg == '8':
        return "EE"


def algo_to_arduino(msg):
    if msg == "SE":
        return '4'
    elif msg == "M":
        return '0'
    elif msg == "R":
        return '1'
    elif msg == "L":
        return '2'
    elif msg == "B":
        return '3'
    elif msg == "SF":
        return '5'
    elif msg == "EE":
        return 8
    elif msg == "CF":
        return "i"
