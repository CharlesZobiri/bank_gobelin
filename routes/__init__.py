from .auth import router as auth_router
from .accounts import router as accounts_router
from .transfer import router as transfer_router
from .beneficiaries import router as beneficiaries_router

__all__ = ['auth_router', 'accounts_router', 'transfer_router', 'beneficiaries_router']