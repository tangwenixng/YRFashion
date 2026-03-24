from collections.abc import Callable, Coroutine
from types import MethodType
from typing import Any

from fastapi.routing import APIRoute
from starlette.requests import Request
from starlette.responses import Response

from backend.services.storage import MAX_IMAGE_SIZE_BYTES


def _upload_size_form(
    request: Request,
    *,
    max_files: int | float = 1000,
    max_fields: int | float = 1000,
    max_part_size: int = MAX_IMAGE_SIZE_BYTES,
):
    return Request.form(
        request,
        max_files=max_files,
        max_fields=max_fields,
        max_part_size=max_part_size,
    )


class UploadSizeRoute(APIRoute):
    def get_route_handler(self) -> Callable[[Request], Coroutine[Any, Any, Response]]:
        original_route_handler = super().get_route_handler()

        async def custom_route_handler(request: Request) -> Response:
            request.form = MethodType(_upload_size_form, request)
            return await original_route_handler(request)

        return custom_route_handler
