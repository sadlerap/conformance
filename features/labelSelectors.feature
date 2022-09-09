Feature: Bind workloads matching a label selector to a service

    As a user, I want to bind workloads that match a particular label selector

    Background:
        Given Namespace [TEST_NAMESPACE] is used
        And The Secret is present
            """
            apiVersion: v1
            kind: Secret
            metadata:
                name: $scenario_id
            stringData:
                username: foo
                password: bar
                type: baz
            """

    Scenario: Bind a workload matching a label selector to a service
        Given Generic test application "$scenario_id" is running with label "app-custom=$scenario_id"
        When Service Binding is applied
            """
            apiVersion: servicebinding.io/v1beta1
            kind: ServiceBinding
            metadata:
                name: $scenario_id
            spec:
                service:
                    apiVersion: v1
                    kind: Secret
                    name: $scenario_id
                workload:
                    apiVersion: apps/v1
                    kind: Deployment
                    selector:
                        matchLabels:
                            app-custom: $scenario_id
            """
        Then Service Binding becomes ready
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
            baz
            """

    Scenario: Bind two workloads to a single service
        Given Generic test application "$scenario_id-1" is running with label "app-custom=$scenario_id"
        And Generic test application "$scenario_id-2" is running with label "app-custom=$scenario_id"
        When Service Binding is applied
            """
            apiVersion: servicebinding.io/v1beta1
            kind: ServiceBinding
            metadata:
                name: $scenario_id
            spec:
                service:
                    apiVersion: v1
                    kind: Secret
                    name: $scenario_id
                workload:
                    apiVersion: apps/v1
                    kind: Deployment
                    selector:
                        matchLabels:
                            app-custom: $scenario_id
            """
        Then Service Binding becomes ready
        And The projected binding "$scenario_id" in workload "$scenario_id-1" has "username" set to
            """
            foo
            """
        And The projected binding "$scenario_id" in workload "$scenario_id-1" has "password" set to
            """
            bar
            """
        And The projected binding "$scenario_id" in workload "$scenario_id-1" has "type" set to
            """
            baz
            """
        And The projected binding "$scenario_id" in workload "$scenario_id-2" has "username" set to
            """
            foo
            """
        And The projected binding "$scenario_id" in workload "$scenario_id-2" has "password" set to
            """
            bar
            """
        And The projected binding "$scenario_id" in workload "$scenario_id-2" has "type" set to
            """
            baz
            """

    Scenario: Bind a labeled workload submitted after the service binding
        Given Service Binding is applied
            """
            apiVersion: servicebinding.io/v1beta1
            kind: ServiceBinding
            metadata:
                name: $scenario_id
            spec:
                service:
                    apiVersion: v1
                    kind: Secret
                    name: $scenario_id
                workload:
                    apiVersion: apps/v1
                    kind: Deployment
                    selector:
                        matchLabels:
                            app-custom: $scenario_id
            """
        When Generic test application "$scenario_id" is running with label "app-custom=$scenario_id"
        Then Service Binding becomes ready
        And The projected binding "$scenario_id" in workload "$scenario_id" has "username" set to
            """
            foo
            """
        And The projected binding "$scenario_id" in workload "$scenario_id" has "password" set to
            """
            bar
            """
        And The projected binding "$scenario_id" in workload "$scenario_id" has "type" set to
            """
            baz
            """

    Scenario: Bind labeled workloads with a already successful service binding
        Given Generic test application "$scenario_id-1" is running with label "app-custom=$scenario_id"
        And Service Binding is applied
            """
            apiVersion: servicebinding.io/v1beta1
            kind: ServiceBinding
            metadata:
                name: $scenario_id
            spec:
                service:
                    apiVersion: v1
                    kind: Secret
                    name: $scenario_id
                workload:
                    apiVersion: apps/v1
                    kind: Deployment
                    selector:
                        matchLabels:
                            app-custom: $scenario_id
            """
        And Service Binding becomes ready
        When Generic test application "$scenario_id-2" is running with label "app-custom=$scenario_id"
        Then Service Binding becomes ready
        And The projected binding "$scenario_id" in workload "$scenario_id-1" has "username" set to
            """
            foo
            """
        And The projected binding "$scenario_id" in workload "$scenario_id-1" has "password" set to
            """
            bar
            """
        And The projected binding "$scenario_id" in workload "$scenario_id-1" has "type" set to
            """
            baz
            """
        And The projected binding "$scenario_id" in workload "$scenario_id-2" has "username" set to
            """
            foo
            """
        And The projected binding "$scenario_id" in workload "$scenario_id-2" has "password" set to
            """
            bar
            """
        And The projected binding "$scenario_id" in workload "$scenario_id-2" has "type" set to
            """
            baz
            """

    Scenario: Changing a workload's label unbinds the service
        Given Generic test application "$scenario_id" is running with label "app-custom=$scenario_id-1"
        And Service Binding is applied
            """
            apiVersion: servicebinding.io/v1beta1
            kind: ServiceBinding
            metadata:
                name: $scenario_id
            spec:
                service:
                    apiVersion: v1
                    kind: Secret
                    name: $scenario_id
                workload:
                    apiVersion: apps/v1
                    kind: Deployment
                    selector:
                        matchLabels:
                            app-custom: $scenario_id-1
            """
        And Service Binding becomes ready
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
            baz
            """
        When Generic test application "$scenario_id" is running with label "app-custom=$scenario_id-2"
        Then The projected binding key "username" is unavailable
        And The projected binding key "password" is unavailable
        And The projected binding key "type" is unavailable
