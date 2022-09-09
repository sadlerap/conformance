import re
import time
import base64
import json
import yaml
from environment import ctx
from command import Command


class Cluster(object):
    def __init__(self):
        self.cmd = Command()
        self.deployment_template = '''
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: '{name}'
  namespace: {namespace}
  labels:
    app: myapp
spec:
  selector:
    matchLabels:
      app: myapp
  template:
    metadata:
      labels:
        app: myapp
    spec:
      containers:
      - name: myapp
        image: {image_name}
'''

    def get_resource_lst(self, resource_plural, namespace):
        output, exit_code = self.cmd.run(f'{ctx.cli} get {resource_plural} -n {namespace} -o "jsonpath={{.items[*].metadata.name}}"')
        assert exit_code == 0, f"Getting resource list failed as the exit code is not 0 with output - {output}"
        if len(output.strip()) == 0:
            return list()
        else:
            return output.split(" ")

    def search_item_in_lst(self, lst, search_pattern):
        for item in lst:
            if re.fullmatch(search_pattern, item) is not None:
                print(f"item matched {item}")
                return item
        print("Given item not matched from the list of pods")
        return None

    def search_resource_in_namespace(self, resource_plural, name_pattern, namespace):
        print(f"Searching for {resource_plural} that matches {name_pattern} in {namespace} namespace")
        lst = self.get_resource_lst(resource_plural, namespace)
        if len(lst) != 0:
            print("Resource list is {}".format(lst))
            return self.search_item_in_lst(lst, name_pattern)
        else:
            print('Resource list is empty under namespace - {}'.format(namespace))
            return None

    def apply(self, yaml, namespace=None, user=None, validate=False):
        if namespace is not None:
            ns_arg = f"-n {namespace}"
        else:
            ns_arg = ""
        if user is not None:
            user_arg = f"--user={user}"
        else:
            user_arg = ""
        (output, exit_code) = self.cmd.run(f"{ctx.cli} apply {ns_arg} {user_arg} --validate={validate} -f -", yaml)
        assert exit_code == 0, f"Non-zero exit code ({exit_code}) while applying a YAML: {output}"
        return output

    def apply_invalid(self, yaml, namespace=None):
        if namespace is not None:
            ns_arg = f"-n {namespace}"
        else:
            ns_arg = ""
        (output, exit_code) = self.cmd.run(f"{ctx.cli} apply {ns_arg} -f -", yaml)
        assert exit_code != 0, f"the command should fail but it did not, output: {output}"
        return output

    def delete(self, yaml, namespace=None):
        if namespace is not None:
            ns_arg = f"-n {namespace}"
        else:
            ns_arg = ""
        (output, exit_code) = self.cmd.run(f"{ctx.cli} delete {ns_arg} -f -", yaml)
        assert exit_code == 0, f"Non-zero exit code ({exit_code}) while deleting a YAML: {output}"
        return output

    def expose_service_route(self, name, namespace, port=""):
        output, exit_code = self.cmd.run(f'{ctx.cli} expose deployment {name} -n {namespace} --port={port} --type=NodePort')
        assert exit_code == 0, f"Could not expose deployment: {output}"

    def get_route_host(self, name, namespace):
        addr = self.get_node_address()
        output, exit_code = self.cmd.run(f'{ctx.cli} get service {name} -n {namespace} -o "jsonpath={{.spec.ports[0].nodePort}}"')
        host = f"{addr}:{output}"

        assert exit_code == 0, f"Getting route host failed as the exit code is not 0 with output - {output}"

        return host

    def get_node_address(self):
        output, exit_code = self.cmd.run(f'{ctx.cli} get nodes -o "jsonpath={{.items[0].status.addresses}}"')
        assert exit_code == 0, f"Error accessing Node resources - {output}"
        addresses = json.loads(output)
        for addr in addresses:
            if addr['type'] in ["InternalIP", "ExternalIP"]:
                return addr['address']
        assert False, f"No IP addresses found in {output}"

    def get_resource_info_by_jsonpath(self, resource_type, name, namespace=None, json_path="{.*}", user=None):
        cmd = f'{ctx.cli} get {resource_type} {name} -o "jsonpath={json_path}"'
        if namespace is not None:
            cmd += f" -n {namespace}"
        if user:
            cmd += f" --user={user}"
        output, exit_code = self.cmd.run(cmd)
        if exit_code == 0:
            if resource_type == "secrets":
                return base64.decodebytes(bytes(output, 'utf-8')).decode('utf-8')
            else:
                return output
        else:
            print(f'Error getting value for {resource_type}/{name} in {namespace} path={json_path}: {output}')
            return None

    def get_resource_info_by_jq(self, resource_type, name, namespace, jq_expression, wait=False, interval=5, timeout=120):
        output, exit_code = self.cmd.run(f'{ctx.cli} get {resource_type} {name} -n {namespace} -o json | jq  \'{jq_expression}\'')
        return output

    def get_deployment_name_in_namespace(self, deployment_name_pattern, namespace, wait=False, interval=5, timeout=120, resource="deployment"):
        if wait:
            start = 0
            while ((start + interval) <= timeout):
                deployment = self.search_resource_in_namespace(resource, deployment_name_pattern, namespace)
                if deployment is not None:
                    return deployment
                time.sleep(interval)
                start += interval
            return None
        else:
            return self.search_resource_in_namespace(resource, deployment_name_pattern, namespace)

    def get_resource_list_in_namespace(self, resource_plural, name_pattern, namespace):
        print(f"Searching for {resource_plural} that matches {name_pattern} in {namespace} namespace")
        lst = self.get_resource_lst(resource_plural, namespace)
        if len(lst) != 0:
            print("Resource list is {}".format(lst))
            return self.get_all_matched_pattern_from_lst(lst, name_pattern)
        else:
            print('Resource list is empty under namespace - {}'.format(namespace))
            return []

    def get_all_matched_pattern_from_lst(self, lst, search_pattern):
        output_arr = []
        for item in lst:
            if re.fullmatch(search_pattern, item) is not None:
                print(f"item matched {item}")
                output_arr.append(item)
        if not output_arr:
            print("Given item not matched from the list of pods")
            return []
        else:
            return output_arr

    def search_resource_lst_in_namespace(self, resource_plural, name_pattern, namespace):
        print(f"Searching for {resource_plural} that matches {name_pattern} in {namespace} namespace")
        lst = self.get_resource_list_in_namespace(resource_plural, name_pattern, namespace)
        if len(lst) != 0:
            print("Resource list is {}".format(lst))
            return lst
        print('Resource list is empty under namespace - {}'.format(namespace))
        return None

    def apply_yaml_file(self, yaml, namespace=None, validate=False):
        if namespace is not None:
            ns_arg = f"-n {namespace}"
        else:
            ns_arg = ""
        (output, exit_code) = self.cmd.run(f"{ctx.cli} apply {ns_arg} --validate={validate} -f " + yaml)
        assert exit_code == 0, "Applying yaml file failed as the exit code is not 0"
        return output

    def new_app(self, name, image_name, namespace, bindingRoot=None):
        formatted = self.deployment_template.format(name=name, image_name=image_name, namespace=namespace, bindingRoot=bindingRoot)
        if bindingRoot is not None:
            parsed = yaml.safe_load(formatted)
            for obj in parsed['spec']['template']['spec']['containers']:
                obj['env'] = [{'name': 'SERVICE_BINDING_ROOT', 'value': bindingRoot}]
            formatted = yaml.dump(parsed)
        self.apply(formatted, namespace=namespace)

    def set_label(self, name, label, namespace):
        cmd = f"{ctx.cli} label deployments {name} '{label}' -n {namespace} --overwrite"
        (output, exit_code) = self.cmd.run(cmd)
        assert exit_code == 0, f"Non-zero exit code ({exit_code}) returned when attempting set label: {cmd}\n: {output}"

    def cli(self, cmd, namespace):
        output, exit_status = self.cmd.run(f'{ctx.cli} {cmd} -n {namespace}')
        assert exit_status == 0, "Exit should be zero"
        return output
