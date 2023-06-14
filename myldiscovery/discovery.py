import logging
import os
import re
import shutil

import dns.resolver
import requests
import xmltodict

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
    res = resolve_txt(domain, criteria="^mailconf=")
    if not res:
        return
    return res.split("=")[1]


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
        },
        "smtp": {
            "server": smtp.get("hostname"),
            "port": int(smtp.get("port")),
            "starttls": smtp.get("socketType") == "STARTTLS",
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
        },
        "smtp": {
            "server": smtp.get("Server"),
            "port": int(smtp.get("Port")),
            "starttls": smtp.get("Encryption", "").lower() == "tls",
        },
    }


def autodiscover_srv(domain):
    imap = resolve_srv(f"_imaps._tcp.{domain}")
    smtp = resolve_srv(f"_submission._tcp.{domain}")

    return {
        "imap": {
            "server": imap[0].get("hostname"),
            "port": int(imap[0].get("port")),
            # FIXME We might want to "smartly" guess if starttls should be
            # enabled or not, depending on the port:
            # 143 -> starttls
            # 993 -> no
            "starttls": False,
        },
        "smtp": {
            "server": smtp[0].get("hostname"),
            "port": int(smtp[0].get("port")),
            # FIXME We might want to "smartly" guess if starttls should be
            # enabled or not, depending on the port:
            # 465 -> starttls
            # 587 -> no
            "starttls": False,
        },
    }


def autodiscover(email_addr, srv_only=False):
    domain = email_addr.split("@")[-1]
    if not domain:
        raise ValueError(f"Invalid email address {email_addr}")

    if srv_only:
        return autodiscover_srv(domain)

    autoconfig = autodiscover_txt(domain)

    if not autoconfig:
        return autodiscover_srv(domain)

    res = requests.get(autoconfig)
    res.raise_for_status()

    try:
        return parse_autoconfig(res.text)
    except Exception:
        LOGGER.warning("Failed to parse autoconfig, trying autodiscover")
        return parse_autodiscover(res.text)