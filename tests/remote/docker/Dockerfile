# A remote for the end-to-end test: sshd and Beamtime from a wheel of this checkout.
FROM python:3.11-slim
RUN apt-get update && apt-get install -y --no-install-recommends openssh-server \
    && rm -rf /var/lib/apt/lists/* && mkdir -p /run/sshd
COPY *.whl /tmp/
RUN pip install --no-cache-dir /tmp/*.whl && rm /tmp/*.whl
# the test's public key arrives in KEY; root logs in with it only.
CMD ["sh", "-c", "mkdir -p /root/.ssh && echo \"$KEY\" > /root/.ssh/authorized_keys && chmod 700 /root/.ssh && chmod 600 /root/.ssh/authorized_keys && exec /usr/sbin/sshd -D -e -o PermitRootLogin=prohibit-password"]
