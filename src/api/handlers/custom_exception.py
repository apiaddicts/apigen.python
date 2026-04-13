class CustomException(Exception):
    def __init__(self, status_code: int, custom_code: str, msg: str):
        self.status_code = status_code
        self.custom_code = custom_code
        self.msg = msg
