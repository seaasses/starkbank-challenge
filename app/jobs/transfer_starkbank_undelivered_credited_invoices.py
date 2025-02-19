from app.services.starkbank_event_services.implementation import (
    StarkBankEventFetcher,
    StarkBankEventStatusChanger,
)
from app.services.transfer_service.implementation import StarkBankTransferSender
from app.models.types import Transfer
from app.core.config import settings
from app.services.thread_lock.interface import ThreadLock


def transfer_starkbank_undelivered_credited_invoices(thread_lock: ThreadLock):
    event_fetcher = StarkBankEventFetcher(settings.starkbank_project)
    event_status_changer = StarkBankEventStatusChanger(settings.starkbank_project)
    transfer_sender = StarkBankTransferSender(settings.starkbank_project)
    for event in event_fetcher.fetch_undelivered_events():
        lock_key = f"event:{event.id}"
        if thread_lock.lock(lock_key):
            try:
                if event.subscription == "invoice" and event.log["type"] == "credited":
                    transfer_amount = (
                        event.log["invoice"]["amount"] - event.log["invoice"]["fee"]
                    )
                    transfer = Transfer(
                        account=settings.default_account,
                        amount=transfer_amount,
                    )
                    transfer_sender.send(transfer)
                event_status_changer.mark_as_delivered(event.id)
            except Exception:
                pass
            finally:
                thread_lock.unlock(lock_key)
