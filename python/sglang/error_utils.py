from enum import IntEnum

class ExceptionType(IntEnum):
    ERROR_INPUT_FORMAT_ERROR = 507
    GPT_NOT_FOUND_ERROR = 508
    NO_PROMPT_ERROR = 509
    EMPTY_PROMPT_ERROR = 510    
    LONG_PROMPT_ERROR = 511       
    ERROR_STOP_LIST_FORMAT = 512
    CONCURRENCY_LIMIT_ERROR = 513
    UNKNOWN_ERROR = 514
    UNSUPPORTED_OPERATION = 515
    ERROR_GENERATE_CONFIG_FORMAT = 516
    UPDATE_ERROR = 601
    MALLOC_ERROR = 602
    TIMEOUT_ERROR = 603
    

class ValueWithErrorCode(ValueError):
    def __init__(self, message: str, error_code: int, *args: object) -> None:
        super().__init__(message, *args)  # 调用父类构造函数
        self.error_code = error_code  # 存储错误码

    def __str__(self) -> str:
        # 返回包含错误信息和错误码的字符串
        return f"{self.args[0]} (Error Code: {self.error_code})"
