import yaml
import polling2
import json
from behave import step, when, then
from cluster import Cluster
from util import substitute_scenario_id


class ServiceBinding(object):

    cluster = Cluster()
    yamlContent = ""
    crdName = ""
    name = ""
    namespace = ""

    def __init__(self, yamlContent, namespace=None):
        self.yamlContent = yamlContent
        res = yaml.full_load(yamlContent)
        self.name = res["metadata"]["name"]
        self.namespace = namespace
        apiVersion = res["apiVersion"]
        self.crdName = f"servicebindings.{apiVersion.split('/')[0]}"
        self.secretPath = '{.status.binding.name}'

    def create(self, user):
        return self.cluster.apply(self.yamlContent, self.namespace, user)

    def attempt_to_create_invalid(self):
        return self.cluster.apply_invalid(self.yamlContent, self.namespace)

    def get_info_by_jsonpath(self, json_path):
        if json_path.startswith("{"):
            return self.cluster.get_resource_info_by_jsonpath(self.crdName, self.name, self.namespace, json_path)
        else:
            return self.cluster.get_resource_info_by_jq(self.crdName, self.name, self.namespace, json_path)

    def get_secret_name(self):
        output = self.get_info_by_jsonpath(self.secretPath)
        assert output is not None, "Failed to fetch secret name from ServiceBinding"
        return output.strip().strip('"')

    def delete(self):
        self.cluster.delete(self.yamlContent, self.namespace)


@step(u'Service Binding is applied')
def sbr_is_applied(context, user=None):
    if "namespace" in context:
        ns = context.namespace.name
    else:
        ns = None
    resource = substitute_scenario_id(context, context.text)
    binding = ServiceBinding(resource, ns)
    assert binding.create(user) is not None, "Service binding not created"
    context.bindings[binding.name] = binding
    context.sb_secret = ""


@step(u'Service Binding becomes ready')
def operator_is_ready(context, sbr_name=None):
    if sbr_name is None:
        sbr_name = list(context.bindings.values())[0].name
    else:
        sbr_name = substitute_scenario_id(context, sbr_name)
    jq_is(context, '.status.conditions[] | select(.type=="Ready").status', sbr_name, 'True')
    sb = context.bindings[sbr_name]
    generation = sb.get_info_by_jsonpath("{.metadata.generation}")
    assert generation is not None, f"Unable to get Service Binding {sb.name} generation"
    observedGeneration = sb.get_info_by_jsonpath("{.status.observedGeneration}")
    assert observedGeneration is not None, f"Unable to get Service Binding {sb.name} observed generation"
    assert generation == observedGeneration, \
        f"Service binding {sb.name} observed generation ({observedGeneration}) not equal to generation ({generation})"
    context.sb_secret = context.bindings[sbr_name].get_secret_name()


# STEP
@step(u'jq "{jq_expression}" of Service Binding should be changed to "{json_value}"')
def jq_is(context, jq_expression, sbr_name=None, json_value=""):
    if sbr_name is None:
        sbr_name = list(context.bindings.values())[0].name
    else:
        sbr_name = substitute_scenario_id(context, sbr_name)
    json_value = substitute_scenario_id(context, json_value)
    polling2.poll(lambda: json.loads(
        context.bindings[sbr_name].get_info_by_jsonpath(jq_expression)) == json_value,
                  step=5, timeout=800, ignore_exceptions=(json.JSONDecodeError,))
