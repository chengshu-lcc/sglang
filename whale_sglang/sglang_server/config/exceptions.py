

from sglang.error_utils import ExceptionType
class FtRuntimeException(Exception):
    def __init__(self, expcetion_type: ExceptionType, message: str):
        self.expcetion_type = expcetion_type
        self.message = message
        super().__init__(self.message)
