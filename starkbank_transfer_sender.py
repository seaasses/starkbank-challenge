from transfer_sender import TransferSender
from transfer import Transfer
import starkbank


class StarkBankTransferSender(TransferSender):
    def __init__(self, starkbank_project: starkbank.Project):
        self.starkbank_project = starkbank_project

    def send(self, transfer: Transfer):
        transfer = self.__converto_to_starkbank_transfer(transfer)
        starkbank.transfer.create([transfer], user=self.starkbank_project)

    def __converto_to_starkbank_transfer(self, transfer: Transfer):
        return starkbank.Transfer(
            bank_code=transfer.account.bank_code,
            branch_code=transfer.account.branch,
            account_number=transfer.account.account,
            account_type=transfer.account.account_type,
            name=transfer.account.name,
            tax_id=transfer.account.tax_id,
            amount=transfer.amount,
        )
