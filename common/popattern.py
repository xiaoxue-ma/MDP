"""
Mixin class for implementing Publisher-Observer pattern
"""

from abc import abstractmethod,ABCMeta

class BasePublisher():
    _listeners = []

    def notify(self):
        "notify all listeners"
        for listener in self._listeners:
            try:
                listener.update()
            except:
                pass

    def add_change_listener(self,listener):
        "add a listener object, which has update() method"
        self._listeners.append(listener)


class BaseObserver():

    __metaclass__ = ABCMeta

    @abstractmethod
    def update(self):
        raise NotImplementedError("update method not implemented")