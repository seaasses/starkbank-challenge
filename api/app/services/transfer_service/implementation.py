import starkbank
from app.models.types import Transfer
from app.services.transfer_service.interface import TransferSender
from app.services.queue_service.interface import QueueService


class QueueTransferSender(TransferSender):
    def __init__(self, queue_service: QueueService):
        self.queue_service = queue_service

    def send(self, transfer: Transfer):
        transfer_message = self.__converto_to_message(transfer)
        self.queue_service.publish_message(transfer_message)

    def __converto_to_message(self, transfer: Transfer):
        return {
            "type": "transfer",
            "status": "pending_creation",
            "data": {"transfer": transfer.model_dump()},
        }
