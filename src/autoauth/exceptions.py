class BaseNYCUException(Exception):
    """陽明交通大學系統基礎例外類別"""
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class LoginException(BaseNYCUException):
    """處理登入陽明交通大學入口網站時的錯誤"""
    pass


class HRSystemError(BaseNYCUException):
    """處理人事差勤系統的錯誤"""
    pass


class NavigationException(BaseNYCUException):
    """處理系統導航過程中的錯誤"""
    pass


class AttendanceException(BaseNYCUException):
    """處理簽到/簽退相關操作的錯誤"""
    pass


# 更詳細的例外類別
class CredentialsError(LoginException):
    """處理憑證相關錯誤，如缺少用戶名或密碼"""
    pass


class LoginFailedError(LoginException):
    """處理登入失敗的錯誤，如帳號密碼錯誤"""
    pass


class TimeClockSystemError(HRSystemError):
    """處理開啟人事差勤系統時的錯誤"""
    pass


class FrameNavigationError(NavigationException):
    """處理框架導航錯誤"""
    pass


class ElementNotFoundError(NavigationException):
    """處理找不到頁面元素的錯誤"""
    pass


class SignInError(AttendanceException):
    """處理簽到操作的錯誤"""
    pass


class SignOutError(AttendanceException):
    """處理簽退操作的錯誤"""
    pass


class ConfirmationError(AttendanceException):
    """處理確認操作的錯誤"""
    pass