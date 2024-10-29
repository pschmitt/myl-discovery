import logging
import os
import re
import shutil
import socket

import dns.resolver
import requests
import xmltodict
from exchangelib import Account, Credentials

LOGGER = logging.getLogger(__name__)


def is_termux():
    if os.getenv("TERMUX_VERSION"):
        return True

    return shutil.which("termux-info") is not None


def resolve(*args, **kwargs):
    termux = is_termux()
    dns.resolver.default_resolver = dns.resolver.Resolver(
        # Do not attempt to read /etc/resolv.conf on Termux
        configure=not termux
    )
    if termux:
        # Default to Google DNS on Termux
        dns.resolver.default_resolver.nameservers = [
            "8.8.8.8",
            "2001:4860:4860::8888",
            "8.8.4.4",
            "2001:4860:4860::8844",
        ]
    return dns.resolver.resolve(*args, **kwargs)


def resolve_txt(domain, criteria="^mailconf="):
    regex = re.compile(criteria)
    answers = resolve(domain, "TXT")
    for rdata in answers:
        for txt_string in rdata.strings:
            txt_record = txt_string.decode("utf-8")
            if re.search(regex, txt_record):
                return txt_record


def resolve_srv(domain):
    answers = resolve(domain, "SRV")
    data = []
    for rdata in answers:
        entry = {
            "hostname": ".".join(
                [
                    x.decode("utf-8")
                    for x in rdata.target.labels
                    if x.decode("utf-8") != ""
                ]
            ),
            "port": rdata.port,
        }
        data.append(entry)

    return data


def autodiscover_txt(domain):
    try:
        res = resolve_txt(domain, criteria="^mailconf=")
        if not res:
            return
        return res.split("=")[1]
    except Exception:
        LOGGER.warning("Failed to resolve TXT record")


# https://wiki.mozilla.org/Thunderbird:Autoconfiguration:ConfigFileFormat
def parse_autoconfig(content):
    data = xmltodict.parse(content)

    imap = (
        data.get("clientConfig", {})
        .get("emailProvider", {})
        .get("incomingServer")
    )
    smtp = (
        data.get("clientConfig", {})
        .get("emailProvider", {})
        .get("outgoingServer")
    )

    LOGGER.debug(f"imap settings: {imap}")
    LOGGER.debug(f"smtp settings: {smtp}")

    assert imap is not None
    assert smtp is not None

    return {
        "imap": {
            "server": imap.get("hostname"),
            "port": int(imap.get("port")),
            "starttls": imap.get("socketType") == "STARTTLS",
            "ssl": imap.get("socketType") == "SSL",
        },
        "smtp": {
            "server": smtp.get("hostname"),
            "port": int(smtp.get("port")),
            "starttls": smtp.get("socketType") == "STARTTLS",
            "ssl": smtp.get("socketType") == "SSL",
        },
    }


def parse_autodiscover(content):
    data = xmltodict.parse(content)
    acc = data.get("Autodiscover", {}).get("Response", {}).get("Account", [])
    imap = next(
        (
            item.get("Protocol", {})
            for item in acc
            if item.get("Protocol", {}).get("Type", "").lower() == "imap"
        ),
        None,
    )
    smtp = next(
        (
            item.get("Protocol", {})
            for item in acc
            if item.get("Protocol", {}).get("Type", "").lower() == "smtp"
        ),
        None,
    )

    LOGGER.debug(f"imap settings: {imap}")
    LOGGER.debug(f"smtp settings: {smtp}")

    assert imap is not None
    assert smtp is not None

    return {
        "imap": {
            "server": imap.get("Server"),
            "port": int(imap.get("Port")),
            "starttls": imap.get("Encryption", "").lower() == "tls",
            # FIXME Is that really the expected value for SSL?
            "ssl": imap.get("Encryption", "").lower() == "ssl",
        },
        "smtp": {
            "server": smtp.get("Server"),
            "port": int(smtp.get("Port")),
            "starttls": smtp.get("Encryption", "").lower() == "tls",
            # FIXME Is that really the expected value for SSL?
            "ssl": smtp.get("Encryption", "").lower() == "ssl",
        },
    }


# https://datatracker.ietf.org/doc/html/rfc6186
def autodiscover_srv(domain):
    try:
        # Start by looking for IMAPS and SUBMISSIONS (ie SSL)
        imap_ssl = True
        smtp_ssl = True
        imap = resolve_srv(f"_imaps._tcp.{domain}")
        smtp = resolve_srv(f"_submissions._tcp.{domain}")

        if not imap:
            LOGGER.warning("No imaps SRV found, trying imap (starttls)")
            imap_ssl = False
            imap = resolve_srv(f"_imap._tcp.{domain}")
        if not smtp:
            LOGGER.warning(
                "No submissions SRV found, trying submission (starttls)"
            )
            imap_ssl = False
            smtp = resolve_srv(f"_submission._tcp.{domain}")

        imap_starttls = not imap_ssl
        smtp_starttls = not smtp_ssl

        assert imap is not None
        assert smtp is not None

        return {
            "imap": {
                "server": imap[0].get("hostname"),
                "port": int(imap[0].get("port")),
                "starttls": imap_starttls,
                "ssl": imap_ssl,
            },
            "smtp": {
                "server": smtp[0].get("hostname"),
                "port": int(smtp[0].get("port")),
                "starttls": smtp_starttls,
                "ssl": smtp_ssl,
            },
        }
    except Exception as e:
        LOGGER.warning(f"Failed to resolve SRV records: {e}")


def port_check(host, port, timeout=5.0):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(float(timeout))
    try:
        result = sock.connect_ex((host, port))
        return result == 0
    except socket.timeout:
        LOGGER.warning(
            f"Connection to {host}:{port} timed out after {timeout} seconds."
        )
        return False
    except socket.error as e:
        LOGGER.warning(f"Socket error occurred: {e}")
        return False
    finally:
        sock.close()


def check_email_ports(host):
    res = {}
    for port in [25, 465, 587, 993]:
        res[port] = port_check(host, port)
    return res


def autodiscover_exchange(email, password, username=None):
    try:
        if not username:
            username = email
        creds = Credentials(username=username, password=password)
        account = Account(
            primary_smtp_address=email, credentials=creds, autodiscover=True
        )
        return autodiscover_port_scan(account.protocol.server)
    except Exception as e:
        LOGGER.warning(f"Failed to autodiscover Exchange: {e}")


def autodiscover_port_scan(server):
    portscan = check_email_ports(server)
    LOGGER.info(f"Port scan results: {portscan}")

    imap_port = imap_starttls = imap_ssl = None
    if portscan.get(993):
        imap_port = 993
        imap_ssl = True
    elif portscan.get(143):
        imap_port = 143
        imap_ssl = False

    smtp_port = smtp_starttls = smtp_ssl = None
    if portscan.get(465):
        smtp_port = 465
        smtp_ssl = True
    elif portscan.get(587):
        smtp_port = 587
        smtp_ssl = False
    elif portscan.get(25):
        smtp_port = 25
        smtp_ssl = False

    imap_starttls = not imap_ssl if imap_ssl is not None else None
    smtp_starttls = not smtp_ssl if smtp_ssl is not None else None

    return {
        "imap": {
            "server": server,
            "port": imap_port,
            "starttls": imap_starttls,
            "ssl": imap_ssl,
        },
        "smtp": {
            "server": server,
            "port": smtp_port,
            "starttls": smtp_starttls,
            "ssl": smtp_ssl,
        },
    }


def autodiscover_autoconfig(domain):
    autoconfig = autodiscover_txt(domain)

    if not autoconfig:
        LOGGER.warning("Failed to autodiscover using TXT records")
        return

    res = requests.get(autoconfig)
    res.raise_for_status()

    try:
        return parse_autoconfig(res.text)
    except Exception:
        LOGGER.warning("Failed to parse autoconfig, trying autodiscover")
        return parse_autodiscover(res.text)


def autodiscover(email_addr, username=None, password=None):
    domain = email_addr.split("@")[-1]
    if not domain:
        raise ValueError(f"Invalid email address {email_addr}")
    if domain == "gmail.com":
        LOGGER.debug("Gmail detected, skipping autodiscover")
        return {
            "imap": {
                "server": "imap.gmail.com",
                "port": 993,
                "starttls": False,
                "ssl": True,
            },
            "smtp": {
                "server": "smtp.gmail.com",
                "port": 465,
                "starttls": False,
                "ssl": True,
            },
        }

    res = autodiscover_autoconfig(domain)

    if not res:
        res = autodiscover_srv(domain)

    if not res and password:
        res = autodiscover_srv(domain)
        autodiscover_exchange(
            email=email_addr, username=username, password=password
        )

    if not res:
        res = autodiscover_port_scan(domain)

    return res
