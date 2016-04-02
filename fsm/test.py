M_MOVE_FORWARD = "mf"

def combine_move_forawrd(ls):
    "combine the mf messages into mf*<num>"
    result_ls = []
    accumlation = 0
    for i in range(len(ls)):
        if (ls[i]==M_MOVE_FORWARD):
            accumlation += 1
        else:
            if (accumlation>0):
                result_ls.append("{}*{}".format(M_MOVE_FORWARD,accumlation)
                                 if accumlation>1 else M_MOVE_FORWARD)
            result_ls.append(ls[i])
            accumlation = 0
    if (accumlation>0):
        result_ls.append("{}*{}".format(M_MOVE_FORWARD,accumlation)
                                 if accumlation>1 else M_MOVE_FORWARD)
    return result_ls


cmds = ['tl','mf','tr','mf','mf','mf','tr','mf']
print (combine_move_forawrd(cmds))