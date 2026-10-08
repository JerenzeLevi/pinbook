"""Domain errors and their HTTP translation."""
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class ContactNotFoundError(Exception):
    def __init__(self, contact_id: int) -> None:
        super().__init__(f"Contact {contact_id} does not exist")
        self.contact_id = contact_id


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(ContactNotFoundError)
    async def _not_found(_: Request, exc: ContactNotFoundError) -> JSONResponse:
        return JSONResponse(
            status_code=404,
            content={"error": {"code": "contact_not_found", "message": str(exc)}},
        )
