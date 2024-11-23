# BSD 2-Clause License

# Copyright (c) 2024, Rashed Abdel-Tawab
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:

# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.

# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.

# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

FROM ubuntu:noble

ENV DEBIAN_FRONTEND=noninteractive
ENV OSMOCOM_REPO="https://downloads.osmocom.org/packages/osmocom:/latest/xUbuntu_24.04"

# Install updates and dependencies
RUN apt update && \
    apt -y install wget gnupg git python3-dev

# Add osmocom repo
RUN wget $OSMOCOM_REPO/Release.key && \
    mv Release.key /etc/apt/trusted.gpg.d/osmocom-latest.asc && \
    echo "deb [signed-by=/etc/apt/trusted.gpg.d/osmocom-latest.asc] $OSMOCOM_REPO/ ./" > /etc/apt/sources.list.d/osmocom-latest.list && \
    apt update

# Install osmo-python-tests
RUN apt -y install osmo-python-tests

# Clone Ki/OPc Generator
#RUN git clone https://github.com/iotconnectivity/kiopcgenerator /etc/kiopcgenerator

# Install Ki/OPc Generator
RUN pip install git+https://github.com/iotconnectivity/kiopcgenerator#egg=kiopcgenerator

# Clone pySim
RUN git clone https://gitea.osmocom.org/sim-card/pysim.git /etc/pysim

# Add scripts
ADD program_and_add.py /program_and_add.py
ADD add_subscriber.py /add_subscriber.py
ADD gen_pair.sh /gen_pair.sh
ADD program_sim.sh /program_sim.sh
ADD sim-carrier-app.script /sim-carrier-app.script
RUN chmod 755 /program_and_add.py /add_subscriber.py /gen_pair.sh /program_sim.sh

ENTRYPOINT ["/program_and_add.py"]
