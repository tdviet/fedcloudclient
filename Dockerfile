FROM python:3.14

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# Install IGTF CAs
# hadolint ignore=DL3008,DL3015
RUN curl -fsSL https://repository.egi.eu/sw/production/cas/1/current/GPG-KEY-EUGridPMA-RPM-4 \
        | gpg --dearmor -o /etc/apt/trusted.gpg.d/GPG-KEY-EUGridPMA-RPM-4.gpg \
    && curl -fsSL https://repository.egi.eu/sw/production/cas/1/current/repo-files/egi-trustanchors.list \
        -o /etc/apt/sources.list.d/egi-trustanchors.list \
    && apt-get update \
    && apt-get install -y --install-recommends ca-policy-egi-core \
    && rm -rf /var/lib/apt/lists/*

# Install oidc-agent and jq (both available in the Debian repos)
# hadolint ignore=DL3008
RUN apt-get update \
    && apt-get install -y --no-install-recommends oidc-agent jq \
    && mkdir -p ~/.config/oidc-agent/ \
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
