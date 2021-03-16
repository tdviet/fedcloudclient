FROM python:3.9.2

# Install IGTF CAs
RUN curl http://repository.egi.eu/sw/production/cas/1/current/repo-files/egi-trustanchors.list \
        > /etc/apt/sources.list.d/egi-trustanchors.list \
    && curl https://dl.igtf.net/distribution/igtf/current/GPG-KEY-EUGridPMA-RPM-3 \
        | apt-key add - \
    && apt-get update \
    && apt-get install -y ca-policy-egi-core

# Install oidc-agent
RUN apt-key adv --keyserver hkp://pgp.surfnet.nl --recv-keys ACDFB08FDC962044D87FF00B512839863D487A87 \
    && echo "deb http://repo.data.kit.edu/debian/buster ./" >> /etc/apt/sources.list.d/oidc-agent.list \
    && apt-get update \
    && apt-get install -y oidc-agent \
    && mkdir -p  ~/.config/oidc-agent/

# Install haveged for workaround the low entropy issue in Cloud that can freeze libsodium initialization
RUN apt-get install haveged

# Install fedcloudclient
COPY . /tmp/fedcloudclient
RUN pip install /tmp/fedcloudclient

# Add IGTF CAs to Python requests
RUN cat /etc/grid-security/certificates/*.pem >> $(python -m requests.certs)

# Save site configs
RUN fedcloud site save-config

CMD ["/usr/local/bin/fedcloud"]
