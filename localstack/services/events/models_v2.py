from dataclasses import dataclass, field
from typing import Optional, TypedDict

from localstack.aws.api.core import ServiceException
from localstack.aws.api.events import (
    Arn,
    CreatedBy,
    EventBusName,
    EventPattern,
    ManagedBy,
    RoleArn,
    RuleDescription,
    RuleName,
    RuleState,
    ScheduleExpression,
    TagList,
)
from localstack.services.stores import (
    AccountRegionBundle,
    BaseStore,
    LocalAttribute,
)


@dataclass
class Rule:
    name: RuleName
    region: str
    account_id: str
    schedule_expression: Optional[ScheduleExpression] = None
    event_pattern: Optional[EventPattern] = None
    state: Optional[RuleState] = None
    description: Optional[RuleDescription] = None
    role_arn: Optional[RoleArn] = None
    tags: TagList = field(default_factory=list)
    event_bus_name: EventBusName = "default"
    targets: TagList = field(default_factory=list)
    managed_by: Optional[ManagedBy] = None  # can only be set by AWS services
    created_by: CreatedBy = field(init=False)
    arn: Arn = field(init=False)

    def __post_init__(self):
        if self.event_bus_name != "default":
            self.arn = f"arn:aws:events:{self.region}:{self.account_id}:rule/{self.event_bus_name}/{self.name}"
        else:
            self.arn = f"arn:aws:events:{self.region}:{self.account_id}:rule/{self.name}"
        self.created_by = self.account_id
        if self.tags is None:
            self.tags = []
        if self.targets is None:
            self.targets = []
        if self.state is None:
            self.state = RuleState.ENABLED


RuleDict = dict[RuleName, Rule]


@dataclass
class EventBus:
    name: EventBusName
    region: str
    account_id: str
    event_source_name: Optional[str] = None
    tags: TagList = field(default_factory=list)
    policy: Optional[str] = None
    rules: RuleDict = field(default_factory=dict)
    arn: Arn = field(init=False)

    def __post_init__(self):
        self.arn = f"arn:aws:events:{self.region}:{self.account_id}:event-bus/{self.name}"
        if self.rules is None:
            self.rules = {}
        if self.tags is None:
            self.tags = []


EventBusDict = dict[EventBusName, EventBus]


class Event(TypedDict, total=False):
    version: str
    id: str
    source: str
    account: str
    time: str
    region: str
    resources: list[str]
    detail_type: str
    detail: dict
    additional_attributes: dict


EventList = list[Event]


class EventsStore(BaseStore):
    # Map of eventbus names to eventbus objects. The name MUST be unique per account and region (works with AccountRegionBundle)
    event_buses: EventBusDict = LocalAttribute(default=dict)


events_store = AccountRegionBundle("events", EventsStore)


#######
# Types
#######


class ValidationException(ServiceException):
    code: str = "ValidationException"
    sender_fault: bool = True
    status_code: int = 400
