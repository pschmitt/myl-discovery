# myl-discovery

Email autoconfig library

## Installation

```shell
pip install myl-discovery
```

## Usage

```python
from myldiscovery import autodiscover
autodiscover("me@example.com")
# {'imap': {'server': 'mail.example.com', 'port': 993, 'starttls': False},
#  'smtp': {'server': 'mail.example.com', 'port': 587, 'starttls': False}}
```


