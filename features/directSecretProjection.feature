Feature: Bind values from a secret referred in backing service resource

    As a user, I would like to inject into my app values from a secret referred
    to by the service binding

    Background:
        Given Namespace [TEST_NAMESPACE] is used
    
    Scenario: Inject binding to a workload from a Secret resource referred as service
        Given The Secret is present
            """
            apiVersion: v1
            kind: Secret
            metadata:
                name: $scenario_id
            stringData:
                username: foo
                password: bar
                type: db
            """
        And Generic test application is running
        When Service Binding is applied
            """
            apiVersion: servicebinding.io/v1beta1
            kind: ServiceBinding
            metadata:
                name: $scenario_id-binding
            spec:
                service:
                    apiVersion: v1
                    kind: Secret
                    name: $scenario_id
                workload:
                    name: $scenario_id
                    apiVersion: apps/v1
                    kind: Deployment
            """
        Then Service Binding becomes ready
        And Content of file "/bindings/$scenario_id-binding/username" in workload pod is
            """
            foo
            """
        And Content of file "/bindings/$scenario_id-binding/password" in workload pod is
            """
            bar
            """
        And Content of file "/bindings/$scenario_id-binding/type" in workload pod is
            """
            db
            """

    Scenario: Bind a workload before the secret is created
        Given Generic test application is running
        And Service Binding is applied
            """
            apiVersion: servicebinding.io/v1beta1
            kind: ServiceBinding
            metadata:
                name: $scenario_id-binding
            spec:
                service:
                    apiVersion: v1
                    kind: Secret
                    name: $scenario_id
                workload:
                    name: $scenario_id
                    apiVersion: apps/v1
                    kind: Deployment
            """
        When The Secret is present
            """
            apiVersion: v1
            kind: Secret
            metadata:
                name: $scenario_id
            stringData:
                username: foo
                password: bar
                type: db
            """
        Then Service Binding becomes ready

    Scenario: Altering a secret after using it in a binding should reflect new values
        Given The Secret is present
            """
            apiVersion: v1
            kind: Secret
            metadata:
                name: $scenario_id
            stringData:
                username: foo
                password: bar
                type: db
            """
        And Generic test application is running
        And Service Binding is applied
            """
            apiVersion: servicebinding.io/v1beta1
            kind: ServiceBinding
            metadata:
                name: $scenario_id-binding
            spec:
                service:
                    apiVersion: v1
                    kind: Secret
                    name: $scenario_id
                workload:
                    name: $scenario_id
                    apiVersion: apps/v1
                    kind: Deployment
            """
        And Service Binding becomes ready
        And Content of file "/bindings/$scenario_id-binding/username" in workload pod is
            """
            foo
            """
        And Content of file "/bindings/$scenario_id-binding/password" in workload pod is
            """
            bar
            """
        And Content of file "/bindings/$scenario_id-binding/type" in workload pod is
            """
            db
            """
        When The Secret is present
            """
            apiVersion: v1
            kind: Secret
            metadata:
                name: $scenario_id
            stringData:
                username: spam
                password: eggs
                type: ham
            """
        Then Content of file "/bindings/$scenario_id-binding/username" in workload pod is
            """
            spam
            """
        And Content of file "/bindings/$scenario_id-binding/password" in workload pod is
            """
            eggs
            """
        And Content of file "/bindings/$scenario_id-binding/type" in workload pod is
            """
            ham
            """
