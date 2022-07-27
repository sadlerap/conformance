# @mark.steps
# ----------------------------------------------------------------------------
# STEPS:
# ----------------------------------------------------------------------------
import os
import re
import yaml
import json

from behave import given, step
from cluster import Cluster
from util import substitute_scenario_id


@given(u'CRD "{backend_service}" is available')
def operator_manifest_installed(context, backend_service=None):
    cluster = Cluster()
    if "namespace" in context:
        ns = context.namespace.name
    else:
        ns = None

    if backend_service is None:
        _ = cluster.apply_yaml_file(os.path.join(os.getcwd(), "resources/backend_crd.yaml"), namespace=ns)
    else:
        _ = cluster.apply_yaml_file(os.path.join(os.getcwd(), "resources/", backend_service + ".operator.manifest.yaml"), namespace=ns)


# STEP
@given(u'The Custom Resource is present')
@step(u'The Secret is present')
def apply_yaml(context):
    cluster = Cluster()
    resource = substitute_scenario_id(context, context.text)
    metadata = yaml.full_load(resource)["metadata"]
    metadata_name = metadata["name"]
    if "namespace" in metadata:
        ns = metadata["namespace"]
    else:
        if "namespace" in context:
            ns = context.namespace.name
        else:
            ns = None
    output = cluster.apply(resource, ns)
    result = re.search(rf'.*{metadata_name}.*(created|unchanged|configured)', output)
    assert result is not None, f"Unable to apply YAML for CR '{metadata_name}': {output}"
    return metadata
