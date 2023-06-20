FROM python:3.11.2

# Get Ubuntu packages
RUN apt-get update && apt-get install -y -q \
    build-essential \
    python3-dev \
    curl

# Get Rust; NOTE: using sh for better compatibility with other base images
RUN curl https://sh.rustup.rs -sSf | sh -s -- -y
# Add .cargo/bin to PATH
ENV PATH="/root/.cargo/bin:${PATH}"


COPY . /mirage
WORKDIR /mirage

# # Create a venv for python (maturin requires it run in a venv)
# RUN python -m venv .venv
# ENV PATH="/mirage/.venv/bin:$PATH"

RUN python -m pip install --upgrade pip

RUN pip install --no-cache-dir .
RUN python setup.py build_ext --inplace
# RUN maturin develop --release

ENV PYTHONPATH "/mirage:${PYTHONPATH}"
# uninstall rust toolchain (it's only needed at build time)
# RUN rustup self uninstall


CMD ["sleep", "inf"]
