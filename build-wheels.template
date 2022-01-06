# from https://github.com/PyO3/setuptools-rust/blob/main/.github/workflows/ci.yml
curl -sSf https://sh.rustup.rs | sh -s -- -y --default-toolchain stable
source ~/.cargo/env
rustup target add $RUST_TARGET
python3.9 -m pip install crossenv
python3.9 -m crossenv "/opt/python/cp39-cp39/bin/python3" --cc $TARGET_CC --cxx $TARGET_CXX --sysroot $TARGET_SYSROOT --env LIBRARY_PATH= --manylinux manylinux1 cross_venv
. cross_venv/bin/activate
pip install wheel setuptools_rust
python setup.py sdist bdist_wheel --py-limited-api=cp39
