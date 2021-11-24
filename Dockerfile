FROM python:3.9


SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# Install IGTF CAs
# hadolint ignore=DL3008,DL3015
RUN curl http://repository.egi.eu/sw/production/cas/1/current/repo-files/egi-trustanchors.list \
        > /etc/apt/sources.list.d/egi-trustanchors.list \
    && curl https://dl.igtf.net/distribution/igtf/current/GPG-KEY-EUGridPMA-RPM-3 \
        | apt-key add - \
    && apt-get update \
    && apt-get install -y --install-recommends ca-policy-egi-core \
    && rm -rf /var/lib/apt/lists/*

# Install oidc-agent and jq
# hadolint ignore=DL3008
RUN apt-key adv --keyserver hkp://pgp.surfnet.nl --recv-keys ACDFB08FDC962044D87FF00B512839863D487A87 \
    && echo "deb http://repo.data.kit.edu/debian/buster ./" >> /etc/apt/sources.list.d/oidc-agent.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends oidc-agent jq \
    && mkdir -p  ~/.config/oidc-agent/ \
    && rm -rf /var/lib/apt/lists/*

COPY . /tmp/fedcloudclient

# Dependencies
RUN pip install --no-cache-dir -r /tmp/fedcloudclient/requirements.txt

# Add IGTF CAs to Python requests
RUN cat /etc/grid-security/certificates/*.pem >> "$(python -m requests.certs)"

# Install fedcloudclient
# hadolint ignore=DL3013
RUN pip install --no-cache-dir /tmp/fedcloudclient

# Post configuration: save site configs and
# make shell more comfortable by adding completion and history
# hadolint ignore=DL3059
RUN fedcloud site save-config \
    && cp /tmp/fedcloudclient/examples/command_history.txt /root/.bash_history \
    && cp /tmp/fedcloudclient/examples/fedcloud_bash_completion.sh /root/.fedcloud_completion \
    && echo ". ~/.fedcloud_completion" > /root/.bashrc

CMD ["/usr/local/bin/fedcloud"]
