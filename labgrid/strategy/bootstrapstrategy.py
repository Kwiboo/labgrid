import enum

import attr

from ..factory import target_factory
from ..step import step
from .common import Strategy, StrategyError, never_retry


class Status(enum.Enum):
    unknown = 0
    off = 1
    on = 2


@target_factory.reg_driver
@attr.s(eq=False)
class BootstrapStrategy(Strategy):
    """BootstrapStrategy - Strategy to bootstrap"""
    bindings = {
        "power": "PowerProtocol",
        "bootstrap": "BootstrapProtocol",
    }

    status = attr.ib(default=Status.unknown)

    def __attrs_post_init__(self):
        super().__attrs_post_init__()

    @never_retry
    @step(args=['status'])
    def transition(self, status):
        if not isinstance(status, Status):
            status = Status[status]
        if status == Status.unknown:
            raise StrategyError(f"can not transition to {status}")
        elif status == self.status:
            return # nothing to do
        elif status == Status.off:
            self.target.activate(self.power)
            self.power.off()
            self.target.deactivate(self.power)
        elif status == Status.on:
            self.target.activate(self.power)
            if not self.power.get():
                self.power.on()
                self.target.activate(self.bootstrap)
                self.bootstrap.load()
                self.target.deactivate(self.bootstrap)
            self.target.deactivate(self.power)
        else:
            raise StrategyError(f"no transition found from {self.status} to {status}")
        self.status = status

    @never_retry
    @step(args=['status'])
    def force(self, status):
        if not isinstance(status, Status):
            status = Status[status]
        if status == Status.off:
            self.target.activate(self.power)
            self.power.off()
            self.target.deactivate(self.power)
        else:
            raise StrategyError("can not force state {}".format(status))
        self.status = status
