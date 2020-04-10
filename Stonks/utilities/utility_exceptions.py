Access_Success = 200


class AccessError(Exception):
    def __init__(self, **kw_arg_list):
        self.kw_args_list = kw_arg_list

        self.TD_Error_Codes = {'the validation problem with the request': 400,
                               'the caller must pass a valid AuthToken in the HTTP authorization request header.': 401,
                               'there was an unexpected server error.': 500,
                               'he caller is forbidden from accessing this page': 403
                               }

        for key, value in self.TD_Error_Codes.items():
            if value == kw_arg_list['ErrorCode']:
                print(key)
            else:
                print('no valid error code passed to exception')


class OrderError(Exception):
    def __init__(self, **kw_arg_list):
        self.kw_args_list = kw_arg_list

        self.TD_Error_Codes = {'a validation problem with the request': 400,
                               'the caller must pass a valid AuthToken in the HTTP authorization request header.': 401,
                               'there was an unexpected server error.': 500,
                               'the caller is forbidden from accessing this page': 403,
                               'the order was not found': 404
                               }

        for key, value in self.TD_Error_Codes.items():
            if value == kw_arg_list['ErrorCode']:
                self.ErrorCode = kw_arg_list['ErrorCode']
                print(key)
            else:
                print('no valid error code passed to exception')


class AccountError(Exception):

    def __init__(self, **kw_arg_list):
        self.kw_args_list = kw_arg_list

        self.TD_Error_Codes = {'a validation problem with the request': 400,
                               'the caller must pass a valid AuthToken in the HTTP authorization request header.': 401,
                               'there was an unexpected server error.': 500,
                               'the caller is forbidden from accessing this page': 403,
                               'the order was not found': 404
                               }

        if 'id_error' in kw_arg_list.keys():
            print('account_id not defined')
