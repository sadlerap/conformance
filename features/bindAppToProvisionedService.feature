Feature: Bind workload to provisioned service

  As a user I would like to bind my applications to provisioned services, as defined by the binding spec

  Background:
    Given Namespace [TEST_NAMESPACE] is used
    And CRD "provisioned_backend" is available
    And The Secret is present
        """
        apiVersion: v1
        kind: Secret
        metadata:
            name: provisioned-secret
        stringData:
            username: foo
            password: bar
            type: db
        """

  Scenario: Bind workload to provisioned service
    Given The Custom Resource is present
        """
        apiVersion: stable.example.com/v1
        kind: ProvisionedBackend
        metadata:
            name: $scenario_id
        spec:
            foo: bar
        status:
            binding:
                name: provisioned-secret
        """
    And Generic test application is running
    When Service Binding is applied
        """
        apiVersion: servicebinding.io/v1beta1
        kind: ServiceBinding
        metadata:
            name: $scenario_id
        spec:
            service:
                apiVersion: stable.example.com/v1
                kind: ProvisionedBackend
                name: $scenario_id
            workload:
                apiVersion: apps/v1
                kind: Deployment
                name: $scenario_id
        """
    Then Service Binding becomes ready
    And jq ".status.binding.name" of Service Binding should be changed to "provisioned-secret"
    And Content of file "/bindings/$scenario_id/username" in workload pod is
        """
        foo
        """
    And Content of file "/bindings/$scenario_id/password" in workload pod is
        """
        bar
        """
    And Content of file "/bindings/$scenario_id/type" in workload pod is
        """
        db
        """

  Scenario: Fall back to a default if SERVICE_BINDING_ROOT is not set
    Given The Custom Resource is present
        """
        apiVersion: stable.example.com/v1
        kind: ProvisionedBackend
        metadata:
            name: $scenario_id
        spec:
            foo: bar
        status:
            binding:
                name: provisioned-secret
        """
    And Generic test application is running
    When Service Binding is applied
        """
        apiVersion: servicebinding.io/v1beta1
        kind: ServiceBinding
        metadata:
          name: $scenario_id
        spec:
            service:
                apiVersion: stable.example.com/v1
                kind: ProvisionedBackend
                name: $scenario_id
            workload:
                apiVersion: apps/v1
                kind: Deployment
                name: $scenario_id
        """
    Then Service Binding becomes ready
    And The service binding root is valid
    And The projected binding "$scenario_id" has "username" set to
        """
        foo
        """
    And The projected binding "$scenario_id" has "password" set to
        """
        bar
        """
    And The projected binding "$scenario_id" has "type" set to
        """
        db
        """

  Scenario: Override type in provisioned service with values from ServiceBinding
    Given The Custom Resource is present
        """
        apiVersion: stable.example.com/v1
        kind: ProvisionedBackend
        metadata:
            name: $scenario_id
        spec:
            foo: bar
        status:
            binding:
                name: provisioned-secret
        """
    And Generic test application is running
    When Service Binding is applied
        """
        apiVersion: servicebinding.io/v1beta1
        kind: ServiceBinding
        metadata:
          name: $scenario_id
        spec:
          service:
            apiVersion: stable.example.com/v1
            kind: ProvisionedBackend
            name: $scenario_id
          type: baz
          workload:
            apiVersion: apps/v1
            kind: Deployment
            name: $scenario_id
        """
    Then Service Binding becomes ready
    And Content of file "/bindings/$scenario_id/username" in workload pod is
        """
        foo
        """
    And Content of file "/bindings/$scenario_id/password" in workload pod is
        """
        bar
        """
    And Content of file "/bindings/$scenario_id/type" in workload pod is
        """
        baz
        """

  Scenario: Override provider in provisioned service with values from ServiceBinding
    Given The Custom Resource is present
        """
        apiVersion: stable.example.com/v1
        kind: ProvisionedBackend
        metadata:
            name: $scenario_id
        spec:
            foo: bar
        status:
            binding:
                name: provisioned-secret
        """
    And Generic test application is running with binding root as "/bindings/external"
    When Service Binding is applied
        """
        apiVersion: servicebinding.io/v1beta1
        kind: ServiceBinding
        metadata:
            name: $scenario_id
        spec:
            service:
              apiVersion: stable.example.com/v1
              kind: ProvisionedBackend
              name: $scenario_id
            workload:
              apiVersion: apps/v1
              kind: Deployment
              name: $scenario_id
        """
    Then Service Binding becomes ready
    And Debug print deployment "$scenario_id"
    And Content of file "/bindings/external/$scenario_id/username" in workload pod is
        """
        foo
        """
    And Content of file "/bindings/external/$scenario_id/password" in workload pod is
        """
        bar
        """
    And Content of file "/bindings/external/$scenario_id/type" in workload pod is
        """
        db
        """

  Scenario: Override provider in provisioned service with values from ServiceBinding
    Given The Custom Resource is present
        """
        apiVersion: stable.example.com/v1
        kind: ProvisionedBackend
        metadata:
            name: $scenario_id
        spec:
            foo: bar
        status:
            binding:
                name: provisioned-secret
        """
    And Generic test application is running
    When Service Binding is applied
        """
        apiVersion: servicebinding.io/v1beta1
        kind: ServiceBinding
        metadata:
            name: $scenario_id
        spec:
            provider: baz
            service:
                apiVersion: stable.example.com/v1
                kind: ProvisionedBackend
                name: $scenario_id
            workload:
                apiVersion: apps/v1
                kind: Deployment
                name: $scenario_id
        """
    Then Service Binding becomes ready
    And Content of file "/bindings/$scenario_id/username" in workload pod is
        """
        foo
        """
    And Content of file "/bindings/$scenario_id/password" in workload pod is
        """
        bar
        """
    And Content of file "/bindings/$scenario_id/type" in workload pod is
        """
        db
        """
    And Content of file "/bindings/$scenario_id/provider" in workload pod is
        """
        baz
        """

  Scenario: Use SERVICE_BINDING_ROOT provided by a workload
    Given The Custom Resource is present
        """
        apiVersion: stable.example.com/v1
        kind: ProvisionedBackend
        metadata:
            name: $scenario_id
        spec:
            foo: bar
        status:
            binding:
                name: provisioned-secret
        """
    And Generic test application is running with binding root as "/bindings/external"
    When Service Binding is applied
        """
        apiVersion: servicebinding.io/v1beta1
        kind: ServiceBinding
        metadata:
            name: $scenario_id
        spec:
            service:
                apiVersion: stable.example.com/v1
                kind: ProvisionedBackend
                name: $scenario_id
            workload:
                apiVersion: apps/v1
                kind: Deployment
                name: $scenario_id
        """
    Then Service Binding becomes ready
    And Content of file "/bindings/external/$scenario_id/username" in workload pod is
        """
        foo
        """
    And Content of file "/bindings/external/$scenario_id/password" in workload pod is
        """
        bar
        """
    And Content of file "/bindings/external/$scenario_id/type" in workload pod is
        """
        db
        """
