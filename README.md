# 📩 myl-discovery

myl-discovery is a Python library designed to detect email settings of a given
email address or domain.

## 📥 Installation

To install myl-discovery, run the following command:

```bash
pip install myl-discovery
```

## 📖 Usage

After installing the package, you can use the `autodiscover` function to
discover the email settings for a domain. Here's an example:

```python
from myldiscovery import autodiscover

settings = autodiscover("yourdomain.com")  # or me@yourdomain.com
print(settings)

# For Exchange autodiscovery you need to provide credentials
settings = autodiscover(
    'me@yourdomain.com',
    username='WORKGROUP\me',
    password='mypassword1234'
)
```

## 📄 Output

The `autodiscover` function returns a dictionary with the detected settings.
The dictionary contains two keys, `imap` and `smtp`, each containing a
dictionary with the keys `server`, `port`, and `starttls`.

Here's an example:

```json
{
  "imap": {
    "server": "imap.yourdomain.com",
    "port": 993,
    "starttls": false,
    "ssl": false
  },
  "smtp": {
    "server": "smtp.yourdomain.com",
    "port": 587,
    "starttls": true,
    "ssl": false
  }
}
```

## 🧩 Autodiscover Functions

myl-discovery exposes several functions to discover email settings:

- `autodiscover`: This function wraps the below function do automatically detect
the right settings. (See Autodiscover strategy for more information)
- `autodiscover_srv`: This function attempts to resolve SRV records for
the domain to discover IMAP and SMTP servers.
- `autodiscover_exchange`: This function attempts to use the Exchange
Autodiscover service to discover email settings. It requires a username and
password.
- `autodiscover_autoconfig`: This function attempts to fetch and parse an
autoconfig XML file from a URL specified in the domain's TXT records.
- `autodiscover_port_scan`: This function performs a port scan on the domain
to discover open IMAP and SMTP ports.

## 🧠 Autodiscover Strategy

The `autodiscover` function uses the following strategy to discover
email settings:

1. It first attempts to use `autodiscover_autoconfig` to discover settings
from an autoconfig/autodiscover URL specified in the domain's TXT records.
2. If that fails, it attempts to use `autodiscover_srv` to discover settings
from the domain's SRV records.
3. If that fails and a password is provided, it attempts to use
`autodiscover_exchange` to discover settings using the
Exchange Autodiscover service (only if credentials were provided)
4. If all else fails, it uses `autodiscover_port_scan` to discover settings by
performing a port scan on the domain.

## 💻 CLI usage

If you do not intend to use the Python library and just want to detect the
connection settings of an arbitrary email, myl-discovery also ships with a
CLI tool.

### 📥 Installation

```shell
pipx install myl-discovery
```

### 📖 Usage

```
$ myl-discovery --help
usage: myl-discovery [-h] [-j] [-d] [-u USERNAME] [-p PASSWORD] EMAIL

positional arguments:
  EMAIL

options:
  -h, --help            show this help message and exit
  -j, --json
  -d, --debug
  -u USERNAME, --username USERNAME
                        Username (Exchange only)
  -p PASSWORD, --password PASSWORD
                        Password (Exchange only)
```

Example:

```
$ myl-discovery user01@gmail.com
 Service          Host                           Port       Encryption
 imap             imap.gmail.com                 993        tls
 smtp             smtp.gmail.com                 587        tls
```

## 📜 License

myl-discovery is licensed under the [GNU General Public License v3.0](LICENSE).

## 📑 Upstream docs

- https://wiki.mozilla.org/Thunderbird:Autoconfiguration:ConfigFileFormat
- https://datatracker.ietf.org/doc/html/rfc6186
