"""
before_step(context, step), after_step(context, step)
    These run before and after every step.
    The step passed in is an instance of Step.
before_scenario(context, scenario), after_scenario(context, scenario)
    These run before and after each scenario is run.
    The scenario passed in is an instance of Scenario.
before_feature(context, feature), after_feature(context, feature)
    These run before and after each feature file is exercised.
    The feature passed in is an instance of Feature.
before_all(context), after_all(context)
    These run before and after the whole shooting match.
"""

from steps.command import Command
from steps.environment import ctx

import behave
import cProfile

cmd = Command()


def before_all(_context: behave.runner.Context):

    service_binding_crd, code = cmd.run(f'{ctx.cli} get crds servicebindings.servicebinding.io -o json')
    assert code == 0, "CRD servicebindings.servicebinding.io not available"

    output, code = cmd.run("jq '.spec.versions[] | select(.served == true) | .name'", stdin=service_binding_crd)
    assert code == 0 and "v1beta1" in output, "CRD servicebindings.servicebinding.io/v1beta1 must be served"
    profiler = cProfile.Profile()
    profiler.enable()
    _context.profiler = profiler


def before_scenario(_context, _scenario):
    _context.bindings = dict()
    _context.workloads = dict()
    output, code = cmd.run(f'{ctx.cli} get ns default -o jsonpath="{{.metadata.name}}"')
    assert code == 0, f"Checking connection to OS cluster by getting the 'default' project failed: {output}"


def after_scenario(_context, _scenario):
    # delete all services that we exposed
    for workload in _context.workloads.values():
        output_code = cmd.run(f'{ctx.cli} delete service -n {workload.namespace} {workload.name}')


def after_all(_context):
    _context.profiler.print_stats()
