<h1>
<p align="center">
<img src="https://github.com/cucapra/pollen/blob/main/pollen_icon.png">
</h1>

Pangenome Graph Queries in Calyx
================================

This is a nascent project to build a DSL-to-hardware compiler using [Calyx][] to implement pangenomic graph queries in the vein of [odgi][].

Getting Started
---------------

### Installation


#### Pollen

Clone this repository using 
```
git clone https://github.com/cucapra/pollen.git
```
and run `flit install -s --user` from the root directory. You may need to install [flit]. Then follow the instructions below to set up our dependencies, `calyx` and `odgi`.


#### Calyx

Follow these [instructions](https://docs.calyxir.org/) to install calyx. You must complete the [first](https://docs.calyxir.org/#compiler-installation) and [third](https://docs.calyxir.org/#installing-the-command-line-driver) sections, but feel free to skip the second. The last step should be running `fud check`, which will report that some tools are unavailable. This is okay for our purposes.

We recommend using the native calyx interpreter. After completing the above, run
```
fud config stages.interpreter <full path to calyx repository>/target/debug/interp
```

Finally, install the [python interface](https://docs.calyxir.org/calyx-py.html) with
```
cd calyx-py && flit install -s
```

#### Odgi

Installing odgi [via bioconda](https://odgi.readthedocs.io/en/latest/rst/installation.html#bioconda) seems to be the most straightforward option. If you instead [compile odgi from source](https://odgi.readthedocs.io/en/latest/rst/installation.html#building-from-source), you will need to [edit your python path](https://odgi.readthedocs.io/en/latest/rst/binding/usage.html) in order to use the python bindings.

To verify that odgi is installed and the python bindings are working, open up a python shell and try `import odgi`. If this works, move on to the next section.

We have encountered two gotchas when installing odgi: a version clash with python, and an issue with odgi's memory manager. Below we describe what we think is a complete installation of odgi that addresses both of these issues.

1. Check your python version with `python --version`. We use python 3.9.12 for the rest of this example.
2. Run `mkdir odgi-py; cd odgi-py`.
3. Download the appropriate tarball (in this example, it will have `py39` in its name) from [bioconda][].
4. Untar it, and run `ls lib/python3.9/site-packages/` to ensure that `odgi.cpython*.so` is there. If it is elsewhere, make note of the location and substitute in the next step.
5. Add this to your `PYTHONPATH` with `export PYTHONPATH=<full path to odgi-py>/lib/python3.9/site-packages/`.
6. Preload `jemalloc`: explore under `/usr/lib/x86_64-linux-gnu/` to ensure that `libjemalloc.so.2` is there. If it is not, search under `/lib/x86_64-linux-gnu/` and substitute in the next step.
7. Run `export LD_PRELOAD=/usr/lib/x86_64-linux-gnu/libjemalloc.so.2`.
8. Open up a python shell and try `import odgi`.

### Generating an Accelerator: Quick

If you want to quickly compute node depth, the following command will generate and run a node depth accelerator:
```
exine depth -a -r <filename.og>
```

This will automatically generate a node depth accelerator whose dimensions match the input data, compute the node depth, and remove the accelerator once the computation is done.

To save the files generated from the previous command in `<path>`, use the `--tmp-dir` flag:
```
exine depth -a -r <filename.og> --tmpdir <path>
```
The node depth accelerator will be saved at `<path>/<filename.futil>` and the input data will be saved at `<path>/<filename.data>`.


Generating an Accelerator: Full Walkthrough
-------------------------------------------

Take [node depth](https://pangenome.github.io/odgi.github.io/rst/commands/odgi_depth.html) as an example. To generate and run a node depth accelerator for the graph `k.og`, first navigate to the root directory of this repository. Then run
```
make fetch
make test/k.og
exine depth -o depth.futil
exine depth -d test/k.og -o depth.data
exine depth -r depth.data --accelerator depth.futil
```

What just happened? Below, we walk through the five commands we issued above, pointing out the other options that we could have used.

First, `make fetch` downloads some [GFA][] data files into the `./test` directory.

Second, `make test/*.og` builds the odgi graph files from those GFA files.

Third, we generate the hardware accelerator and write it to a file named `depth.futil`. The commands to generate a node depth hardware accelerator in calyx include:

1. `exine depth -o depth.futil`
2. `exine depth -a <filename.og> -o depth.futil`
3. `exine depth -n=MAX_NODES -e=MAX_STEPS -p=MAX_PATHS -o depth.futil`

The commands use the hardware parameters as follows:
1. Uses default hardware parameters.
2. Takes the hardware parameters as input.
3. Automatically infers the hardware parameters from a `.og` file.

Parameters that are specified manually take precedence over those that are inferred automatically, and it is legal to specify just a subset of parameters. For example, `exine depth -a test/k.og -n=1` will infer `MAX_STEPS` and `MAX_PATHS` from `test/k.og`, but the resulting accelerator will only handle one node.

Fourth, we need to generate some input from our odgi file. This is what we will feed to the hardware accelerator. The following variations all accomplish this:

1. `exine depth -d <filename.og> -o depth.data`
2. `exine depth -d <filename.og> -a <filename2.og> -o depth.data`
3. `exine depth -d <filename.og> -n=MAX_NODES -e=MAX_STEPS -p=MAX_PATHS -o depth.data`
4. `exine depth -d <filename.og> -a -o depth.data`
    
The flags work as before, except that if no argument is passed to the `-a` flag, the dimensions are inferred from the input file. **The dimensions of the input must be the same as that of the hardware accelerator.**

Fifth, we run our hardware accelerator. The following code simulates the calyx code for the hardware accelerator and outputs the node depth table:

```
exine depth -r depth.data -x depth.futil
```

Testing
-------

To run the core tests, you will need to install [Turnt][]. We rely on version 1.9.0 or later. Then, navigative to the root directory of the pollen repository and run `make test`.

Warning: the tests take approximately 2 hours to complete.

[calyx]: https://calyxir.org
[odgi]: https://odgi.readthedocs.io/en/latest/
[gfa]: https://github.com/lh3/gfatools/blob/master/doc/rGFA.md#the-reference-gfa-rgfa-format
[bioconda]: https://anaconda.org/bioconda/odgi/files
[flit]: https://flit.pypa.io/en/stable/
[turnt]: https://github.com/cucapra/turnt
