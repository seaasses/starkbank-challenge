from app.services.starkbank_event_services.implementation import (
    StarkBankEventFetcher,
    StarkBankEventStatusChanger,
)
from app.services.transfer_service.implementation import StarkBankTransferSender
from app.models.types import Transfer
from app.core.config import settings


def transfer_starkbank_undelivered_credited_invoices():
    event_fetcher = StarkBankEventFetcher(settings.starkbank_project)
    event_status_changer = StarkBankEventStatusChanger(settings.starkbank_project)
    transfer_sender = StarkBankTransferSender(settings.starkbank_project)
    for event in event_fetcher.fetch_undelivered_events():
        try:
            if event.subscription == "invoice" and event.log["type"] == "credited":
                transfer_amount = (
                    event.log["invoice"]["amount"] - event.log["invoice"]["fee"]
                )
                # TODO: batch transfers
                transfer = Transfer(
                    account=settings.default_account,
                    amount=transfer_amount,
                )
                transfer_sender.send(transfer)
            # Only mark as delivered if no exception occurred
            event_status_changer.mark_as_delivered(event.id)
        except Exception:
            # Skip failed events and continue with the next one
            pass
