from app import App
import requests
import json
import polling2
from behave import step
from util import substitute_scenario_id
from string import Template


class GenericTestApp(App):

    deployment_name_pattern = "{name}"

    def __init__(self, name, namespace, app_image="ghcr.io/servicebinding/conformance/generic-test-app:main"):
        super().__init__(name, namespace, app_image, "8080")

    def get_env_var_value(self, name):
        resp = polling2.poll(lambda: requests.get(url=f"http://{self.route_url}/env/{name}"),
                             check_success=lambda r: r.status_code in [200, 404], step=5, timeout=400, ignore_exceptions=(requests.exceptions.ConnectionError,))
        print(f'env endpoint response: {resp.text} code: {resp.status_code}')
        if resp.status_code == 200:
            return json.loads(resp.text)
        else:
            return None

    def format_pattern(self, pattern):
        return pattern.format(name=self.name)

    def get_file_value(self, file_path):
        resp = polling2.poll(lambda: requests.get(url=f"http://{self.route_url}{file_path}"),
                             check_success=lambda r: r.status_code == 200, step=5, timeout=400, ignore_exceptions=(requests.exceptions.ConnectionError,))
        print(f'file endpoint response: {resp.text} code: {resp.status_code}')
        return resp.text

    def set_label(self, label):
        self.cluster.set_label(self.name, label, self.namespace)

    def assert_file_not_exist(self, file_path):
        polling2.poll(lambda: requests.get(url=f"http://{self.route_url}{file_path}"),
                      check_success=lambda r: r.status_code == 404, step=5, timeout=400,
                      ignore_exceptions=(requests.exceptions.ConnectionError,))


@step(u'Generic test application is running')
@step(u'Generic test application is running with binding root as "{bindingRoot}"')
@step(u'Generic test application "{name}" is running with label "{label}"')
def is_running(context, name=None, bindingRoot=None, label=None):
    if name is None:
        workload_name = substitute_scenario_id(context)
    else:
        workload_name = substitute_scenario_id(context, name)

    workload = GenericTestApp(workload_name, context.namespace.name)
    if not workload.is_running():
        print("workload is not running, trying to import it")
        workload.install(bindingRoot=bindingRoot)
    if label is not None:
        workload.set_label(substitute_scenario_id(context, label))
    context.workload = workload
    context.workloads[workload_name] = workload

@step(u'Content of file "{file_path}" in workload pod is')
def check_file_value(context, file_path):
    value = Template(context.text.strip()).substitute(NAMESPACE=context.namespace.name)
    resource = substitute_scenario_id(context, file_path)
    polling2.poll(lambda: context.workload.get_file_value(resource) == value, step=5, timeout=400)

@step(u'The application env var "{name}" has value "{value}"')
def check_env_var_value(context, name, value=None):
    value = substitute_scenario_id(context, value)
    found = polling2.poll(lambda: context.workload.get_env_var_value(name) == value, step=5, timeout=400)
    assert found, f'Env var "{name}" should contain value "{value}"'

@step(u'The service binding root is valid')
def check_binding_root(context, name="SERVICE_BINDING_ROOT"):
    # TODO: check that this is a valid path within the container
    # for now, assert a non-zero-length string
    found = polling2.poll(lambda: context.workload.get_env_var_value(name), step=5, timeout=400)
    assert len(found) != 0, f'Env var "{name}" should be set'

@step(u'The projected binding "{binding_name}" has "{key}" set to')
@step(u'The projected binding "{binding_name}" in workload "{workload_name}" has "{key}" set to')
def check_binding_value(context, binding_name, key, workload_name=None):
    if workload_name is None:
        workload_name = substitute_scenario_id(context)
    else:
        workload_name = substitute_scenario_id(context, workload_name)
    binding_root = polling2.poll(lambda:
            context.workloads[workload_name].get_env_var_value("SERVICE_BINDING_ROOT"),
            step=5, timeout=400)
    binding_path = binding_root + '/' + substitute_scenario_id(context, binding_name) + '/' + key
    check_file_value(context, binding_path)


@step(u'The projected binding key "{key}" is unavailable')
def check_file_unavailable(context, key):
    binding_root = polling2.poll(lambda:
            context.workload.get_env_var_value("SERVICE_BINDING_ROOT"),
            step=5, timeout=400)
    binding_path = binding_root + '/' + substitute_scenario_id(context, context.workload.name) + '/' + key
    context.workload.assert_file_not_exist(binding_path)
