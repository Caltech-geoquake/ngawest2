# Author: Jian Shi

def check_model_name(model_name):
    '''
    Check whether `model_name` is valid. If `model_name` has "14" at the end,
    truncate "14" and keep the rest.
    '''

    if model_name not in ['BSSA','ASK','CB','CY','BSSA14','ASK14','CB14','CY14']:
        raise ValueError("`model_name` must be one of {'ASK', 'BSSA', 'CB', "
                         "'CY', 'ASK14', 'BSSA14', 'CB14', 'CY14'}.")

    if model_name[-2:] == '14':
        model_name = model_name[:-2]

    return model_name

