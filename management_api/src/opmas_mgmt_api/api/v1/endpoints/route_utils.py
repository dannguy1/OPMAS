"""Route utilities for consistent API endpoint management."""

from typing import Any, Callable, Optional, Type, TypeVar, Union

from fastapi import APIRouter, Response, status
from fastapi.types import DecoratedCallable

T = TypeVar("T")


class APIRouteBuilder:
    """Builder class for creating consistent API routes."""

    def __init__(self, router: APIRouter):
        """Initialize with a FastAPI router."""
        self.router = router

    def get(
        self,
        path: str = "",
        *,
        response_model: Optional[Type[T]] = None,
        status_code: int = status.HTTP_200_OK,
        **kwargs: Any,
    ) -> Callable[[DecoratedCallable], DecoratedCallable]:
        """Create a GET endpoint with consistent path handling."""
        return self.router.get(
            path=path, response_model=response_model, status_code=status_code, **kwargs
        )

    def post(
        self,
        path: str = "",
        *,
        response_model: Optional[Type[T]] = None,
        status_code: int = status.HTTP_201_CREATED,
        **kwargs: Any,
    ) -> Callable[[DecoratedCallable], DecoratedCallable]:
        """Create a POST endpoint with consistent path handling."""
        return self.router.post(
            path=path, response_model=response_model, status_code=status_code, **kwargs
        )

    def put(
        self,
        path: str = "",
        *,
        response_model: Optional[Type[T]] = None,
        status_code: int = status.HTTP_200_OK,
        **kwargs: Any,
    ) -> Callable[[DecoratedCallable], DecoratedCallable]:
        """Create a PUT endpoint with consistent path handling."""
        return self.router.put(
            path=path, response_model=response_model, status_code=status_code, **kwargs
        )

    def patch(
        self,
        path: str = "",
        *,
        response_model: Optional[Type[T]] = None,
        status_code: int = status.HTTP_200_OK,
        **kwargs: Any,
    ) -> Callable[[DecoratedCallable], DecoratedCallable]:
        """Create a PATCH endpoint with consistent path handling."""
        return self.router.patch(
            path=path, response_model=response_model, status_code=status_code, **kwargs
        )

    def delete(
        self,
        path: str = "",
        *,
        status_code: int = status.HTTP_204_NO_CONTENT,
        **kwargs: Any,
    ) -> Callable[[DecoratedCallable], DecoratedCallable]:
        """Create a DELETE endpoint with consistent path handling."""
        return self.router.delete(path=path, status_code=status_code, **kwargs)


def create_route_builder(router: APIRouter) -> APIRouteBuilder:
    """Create a route builder for the given router."""
    return APIRouteBuilder(router)
