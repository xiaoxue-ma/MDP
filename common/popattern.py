"""
Mixin class for implementing Publisher-Observer pattern
"""

from abc import abstractmethod,ABCMeta

class BasePublisher():
    _listeners = []

    def notify(self,data=None):
        "notify all listeners"
        for listener in self._listeners:
            try:
                listener.update(data)
            except:
                pass

    def add_change_listener(self,listener):
        "add a listener object, which has update() method"
        self._listeners.append(listener)

class BaseObserver(object):

    __metaclass__ = ABCMeta

    @abstractmethod
    def update(self,data=None):
        raise NotImplementedError("update method not implemented")