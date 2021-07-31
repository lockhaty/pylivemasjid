#Livemasjid

This package provides a pythonic interface to subscribe 
to updates from Livemasjid as well as to get the current
status of Livemasjid streams.

```python
from livemasjid import Livemasjid

def my_callback(topic, message, status):
    print(topic)
    print(message)
    print(status)


if __name__ == "__main__":
    lm = Livemasjid(subscriptions=['activestream'])
    lm.register_on_message_callback(my_callback)
    lm.update_status()
    status = lm.get_status()
    lm.start()
```