FROM messense/manylinux2014-cross:armv7

RUN bash -c "curl -sSf https://sh.rustup.rs | sh -s -- -y --default-toolchain stable && source ~/.cargo/env && rustup target add armv7-unknown-linux-gnueabihf"

