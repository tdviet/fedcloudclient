FROM python:3.8.0

# Install IGTF CAs
RUN curl http://repository.egi.eu/sw/production/cas/1/current/repo-files/egi-trustanchors.list \
         > /etc/apt/sources.list.d/egi-trustanchors.list \
    && curl https://dl.igtf.net/distribution/igtf/current/GPG-KEY-EUGridPMA-RPM-3 \
       | apt-key add - \
    && apt-get update \
    && apt-get install -y ca-policy-egi-core

# Install fedcloudclient
COPY . /tmp/fedcloudclient
RUN pip install /tmp/fedcloudclient

# Add IGTF CAs to Python requests
RUN cat /etc/grid-security/certificates/*.pem >> $(python -m requests.certs)

# Save site configs
RUN fedcloud site save-config

CMD ["/usr/local/bin/fedcloud"]

