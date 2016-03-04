__author__ = 'Boss'
from common import PMessage
from interfaces import real


def parse_to_pm(msg):
    if len(msg) > 1:
        realmsg = PMessage(type=PMessage.T_MAP_UPDATE, msg=msg)
        return realmsg
    else:
        msg = msg[0]
        if msg < '4':
            realmsg = PMessage(type=PMessage.T_ROBOT_MOVE, msg=real.FROM_SER.get(msg[0]))
            return realmsg


def parse_from_pm(msg):
    realmsg = real.TO_SER.get(msg.get_msg())
    if realmsg:
        print "SER--Write to Arduino: %s" % str(realmsg)


if __name__ == "__main__":
    input = raw_input()
    result = parse_to_pm(input)
    print result
    result = parse_from_pm(result)
