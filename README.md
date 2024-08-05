# FreeWavm
FreeWavm: Fuzzing WebAssembly Runtime via Structure-Aware Mutation

## Architecture
1. `pymodules/python-mutators`: The main file of FreeWavm
2. `pymodules/wasm`: The implementation of WebAssembly module parser
3. `pymodules/mutator`: The mutators of FreeWavm

## Quick Start

### Compiling
```
make -j$(nproc)
```

### Running

```
AFL_PYTHON_ONLY=1 AFL_PYTHON_MODULE="pymodules.python-mutators" PYTHONPATH=. ./afl-fuzz -m none -t 500+ -i [input directory with test cases] -o [output directory for fuzzer results] [path to the vm] @@
```

## WebAssembly Corpus
We make our WebAssembly corpus publicly available. [Download](https://drive.google.com/file/d/1eJgGMeEd4dg_RvuSOXP3zQrnxWEBdChJ/view?usp=sharing)
