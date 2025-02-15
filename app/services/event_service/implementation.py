import starkbank
from app.services.event_service.interface import EventFetcher
from app.models.types import StarkBankEvent
from typing import Generator


class StarkBankEventFetcher(EventFetcher):
    def __init__(self, starkbank_project: starkbank.Project):
        self.starkbank_project = starkbank_project

    def fetch_undelivered_events(self) -> Generator[StarkBankEvent, None, None]:
        events = starkbank.event.query(is_delivered=False, user=self.starkbank_project)
        for event in events:
            yield self.__convert_to_application_model(event)

    def __convert_to_application_model(
        self, starkbank_event: starkbank.Event
    ) -> StarkBankEvent:
        log = starkbank_event.log
        log_dict = {
            "id": log.id,
            "created": log.created,
            "type": log.type,
            "errors": log.errors,
        }

        for attr_name in dir(log):
            if attr_name.startswith("_"):
                continue

            if attr_name in log_dict:
                continue

            attr_value = getattr(log, attr_name)

            if callable(attr_value):
                continue

            if hasattr(attr_value, "__dict__"):
                sub_dict = {}
                for sub_attr in dir(attr_value):
                    if sub_attr.startswith("_"):
                        continue
                    sub_value = getattr(attr_value, sub_attr)
                    if not callable(sub_value):
                        sub_dict[sub_attr] = sub_value
                log_dict[attr_name] = sub_dict
            else:
                log_dict[attr_name] = attr_value

        return StarkBankEvent(
            created=starkbank_event.created,
            id=starkbank_event.id,
            log=log_dict,
            subscription=starkbank_event.subscription,
            workspaceId=starkbank_event.workspace_id,
        )
