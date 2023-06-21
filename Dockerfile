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

RUN python -m pip install --upgrade pip

# Copy just enough for `pip install .` to pull in deps without having source code
COPY pyproject.toml /mirage/pyproject.toml
COPY ./mirage_ext /mirage/mirage_ext
COPY Cargo.toml /mirage/Cargo.toml
COPY Cargo.lock /mirage/Cargo.lock
COPY README.md /mirage/README.md

WORKDIR /mirage

# # Create a venv for python (maturin requires it run in a venv)
# RUN python -m venv .venv
# ENV PATH="/mirage/.venv/bin:$PATH"


RUN pip install --no-cache-dir .

COPY . /mirage
RUN python setup.py build_ext --inplace

ENV PYTHONPATH "/mirage:${PYTHONPATH}"
# uninstall rust toolchain (it's only needed at build time)
RUN rustup self uninstall -y


CMD ["sleep", "inf"]
