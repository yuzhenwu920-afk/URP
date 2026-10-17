"""Connect the original frozen Modified DI model here. No proxy fallback."""


def provenance():
    """Return engine='Modified_DI_AquaCrop', deterministic=True and files.

    Each file entry: {role: model_source/weather/soil/irrigation/observations,
                      path: 'relative/to/this/adapter', sha256: 'actual hash'}.
    Include all actual dependencies and model versions, not just one example.
    """
    raise NotImplementedError('2022阶段二包装器和真链已接入；仍缺其导入的原DI_2022_MCMC_ONE_CLICK.py及data，真实模型未接入')


def simulate(*,params,year,management=None):
    """Return OUTPUTS + LEDGER + Y_dry from model_adapter, and actual events.

    management=None uses the original annual baseline; otherwise apply exactly
    the declared SMT or stage_amounts controls. Reset mutable state every call.
    Preserve actual-CC evaporation, MulchPct, two-phase WP and annual HI0.
    Irrigation events: [{date:'YYYY-MM-DD', mm:float, stage:0-based integer}].
    CR and GwIn must be separate additive inflows, with the full-profile ledger.
    """
    raise NotImplementedError('Original frozen model implementation is required')


def management_space(year):
    """Prefer kind=SMT, four names/lower=0/upper=100 and actual definition.

    Also return four allowed_windows=[[start,end],...] from the real module.
    If unsupported, kind=stage_amounts with 4 or 5 names/lower/upper/dates and
    corresponding windows. Do not invent thresholds or dates from proxy plots.
    """
    raise NotImplementedError('Declare and connect the real irrigation controls')
