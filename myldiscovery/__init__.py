import logging
import re

import dns.resolver
import requests
import xmltodict

LOGGER = logging.getLogger(__name__)


def resolve_txt(domain, criteria="^mailconf="):
    regex = re.compile(criteria)
    answers = dns.resolver.resolve(domain, "TXT")
    for rdata in answers:
        for txt_string in rdata.strings:
            txt_record = txt_string.decode("utf-8")
            if re.search(regex, txt_record):
                return txt_record


def resolve_srv(domain):
    answers = dns.resolver.resolve(domain, "SRV")
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


def autodiscover(email_addr, srv_only=False):
    domain = email_addr.split("@")[-1]
    if not domain:
        raise ValueError(f"Invalid email address {email_addr}")

    autoconfig = autodiscover_txt(domain) if not srv_only else None

    if not autoconfig:
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
            }
        }

    res = requests.get(autoconfig)
    res.raise_for_status()

    data = xmltodict.parse(res.text)
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
