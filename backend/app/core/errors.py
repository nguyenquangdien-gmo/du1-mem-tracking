from fastapi import HTTPException, status


class AppError(HTTPException):
    def __init__(self, code: str, message: str, status_code: int = 400, field: str | None = None):
        detail = {"code": code, "message": message}
        if field:
            detail["field"] = field
        super().__init__(status_code=status_code, detail=detail)


def not_found(resource: str = "Resource") -> AppError:
    return AppError("NOT_FOUND", f"{resource} không tồn tại", status.HTTP_404_NOT_FOUND)


def validation_error(message: str, field: str | None = None) -> AppError:
    return AppError("VALIDATION_ERROR", message, status.HTTP_400_BAD_REQUEST, field)


def already_assigned(message: str = "Member đã được assign") -> AppError:
    return AppError("ALREADY_ASSIGNED", message, status.HTTP_409_CONFLICT)


def member_has_active_assignments() -> AppError:
    return AppError(
        "MEMBER_HAS_ACTIVE_ASSIGNMENTS",
        "Không thể xóa member còn assignment active",
        status.HTTP_409_CONFLICT,
    )
