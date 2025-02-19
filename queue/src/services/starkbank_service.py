import starkbank
from ..models.schemas import Invoice, Transfer
from ..config.settings import get_private_key, STARK_PROJECT_ID, STARK_ENVIRONMENT


class StarkbankService:
    def __init__(self):
        starkbank.user = starkbank.Project(
            environment=STARK_ENVIRONMENT,
            id=STARK_PROJECT_ID,
            private_key=get_private_key(),
        )

    def send_invoice(self, invoice: Invoice):
        starkbank_invoice = starkbank.Invoice(
            amount=invoice.amount,
            due=invoice.due_date,
            name=invoice.person.name,
            tax_id=invoice.person.cpf,
        )

        starkbank.invoice.create([starkbank_invoice])

    def create_transfer(self, transfer: Transfer) -> str:
        starkbank_transfer = starkbank.Transfer(
            amount=transfer.amount,
            name=transfer.account.name,
            tax_id=transfer.account.tax_id,
            bank_code=transfer.account.bank_code,
            branch_code=transfer.account.branch,
            account_number=transfer.account.account,
            account_type=transfer.account.account_type,
            rules=starkbank.transfer.Rules(key="resendingLimit", value=5),
        )

        created_transfer = starkbank.transfer.create([starkbank_transfer])
        return created_transfer[0].id

    def get_transfer_status(self, transfer_id: str):
        try:
            transfer = starkbank.transfer.get(transfer_id)
            return transfer.status
        except Exception as e:
            return None
