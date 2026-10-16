"""Fill these two functions from the original Modified DI source, not the proxy.

The runner intentionally cannot execute this template. Do not substitute zeros
for unavailable outputs, infer a missing water flux from the desired balance,
or fit correction factors to force the benchmark to pass.
"""


def provenance():
    """Return a frozen source/input manifest; include all files used by simulate.

    Example structure (hashes must be computed from the actual files):
    {"engine": "Modified_DI_AquaCrop", "deterministic": True,
     "versions": {"aquacrop": "..."},
     "files": [{"role": "model_source", "path": "DI_2019_MCMC_ONE_CLICK.py",
                "sha256": "..."},
               {"role": "input", "path": "data/weather.csv", "sha256": "..."}]}
    Relative paths resolve beside this adapter. The manifest is self-description,
    so source review and the matched baseline check remain necessary.
    """
    raise NotImplementedError("Original Modified DI model source and inputs have not been supplied")


def simulate(*, params, year, management=None):
    """Return the named scalar outputs listed in real_model_pipeline.REQUIRED.

    params: all eight physical parameter names, preserving original units.
    management=None: the ORIGINAL model's frozen annual DI baseline schedule.
    Reset mutable model/data state between calls. Preserve the phase-specific WP
    switch, audited daily ETo, field-locked initial water, evaporation changes,
    and the original full-depth soil/surface water ledger.

    The management argument is reserved for the verified irrigation interface;
    no SMT or fixed-date irrigation conversion has been invented in this kit.
    """
    raise NotImplementedError("Connect the original model; no fallback simulator is provided")
