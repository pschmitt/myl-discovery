## Development

### Autodiscovery

#### autoconfig

```shell
curl -L https://mail.example.com/mail/config-v1.1.xml
```

Response:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<clientConfig version="1.1">
	<emailProvider id="example.com">
	    <domain>example.com</domain>

	    <displayName>example.com Email</displayName>
	    <displayShortName>%EMAILLOCALPART%</displayShortName>
	    <incomingServer type="imap">
			<hostname>mail.example.com</hostname>
			<port>143</port>
			<socketType>STARTTLS</socketType>
			<authentication>password-cleartext</authentication>
			<username>%EMAILADDRESS%</username>
		</incomingServer>
	    <outgoingServer type="smtp">
			<hostname>mail.example.com</hostname>
			<port>587</port>
			<socketType>STARTTLS</socketType>
			<authentication>password-cleartext</authentication>
			<username>%EMAILADDRESS%</username>
	    </outgoingServer>
		<documentation url="https://autodiscover.example.com">
			<descr lang="en">Generic settings page</descr>
			<descr lang="fr">Paramètres généraux</descr>
			<descr lang="es">Configuraciones genéricas</descr>
			<descr lang="de">Allgemeine Beschreibung der Einstellungen</descr>
			<descr lang="ru">Страница общих настроек</descr>
		</documentation>
	</emailProvider>
</clientConfig>
```

### autodiscover

```shell
curl -L mail.example.com/autodiscover/autodiscover.xml
```

Response:

```xml
<?xml version="1.0" encoding="utf-8" ?>
<Autodiscover xmlns="http://schemas.microsoft.com/exchange/autodiscover/responseschema/2006">
        <Response xmlns="http://schemas.microsoft.com/exchange/autodiscover/responseschema/2006">
                <User>
                        <DisplayName>example.com Email</DisplayName>
                </User>
                <Account>
                        <AccountType>email</AccountType>
                        <Action>settings</Action>
                        <ServiceHome>https://autodiscover.example.com</ServiceHome>

                        <Protocol>
                                <Type>IMAP</Type>
                                <TTL>1</TTL>

                                <Server>mail.example.com</Server>
                                <Port>143</Port>

                                <LoginName></LoginName>

                                <DomainRequired>on</DomainRequired>
                                <DomainName>example.com</DomainName>

                                <SPA>off</SPA>
                                <Encryption>TLS</Encryption>
                                <AuthRequired>on</AuthRequired>
                        </Protocol>
                </Account>
                <Account>
                        <AccountType>email</AccountType>
                        <Action>settings</Action>
                        <ServiceHome>https://autodiscover.example.com</ServiceHome>

                        <Protocol>
                                <Type>SMTP</Type>
                                <TTL>1</TTL>

                                <Server>mail.example.com</Server>
                                <Port>587</Port>

                                <LoginName></LoginName>

                                <DomainRequired>on</DomainRequired>
                                <DomainName>example.com</DomainName>

                                <SPA>off</SPA>
                                <Encryption>TLS</Encryption>
                                <AuthRequired>on</AuthRequired>
                        </Protocol>
                </Account></Response>
</Autodiscover>
```

