# LocalStack Resource Provider Scaffolding v2
from __future__ import annotations

from pathlib import Path
from typing import Optional, TypedDict

import localstack.services.cloudformation.provider_utils as util
from localstack.services.cloudformation.resource_provider import (
    OperationStatus,
    ProgressEvent,
    ResourceProvider,
    ResourceRequest,
)


class SecretsManagerSecretProperties(TypedDict):
    Description: Optional[str]
    GenerateSecretString: Optional[GenerateSecretString]
    Id: Optional[str]
    KmsKeyId: Optional[str]
    Name: Optional[str]
    ReplicaRegions: Optional[list[ReplicaRegion]]
    SecretString: Optional[str]
    Tags: Optional[list[Tag]]


class GenerateSecretString(TypedDict):
    ExcludeCharacters: Optional[str]
    ExcludeLowercase: Optional[bool]
    ExcludeNumbers: Optional[bool]
    ExcludePunctuation: Optional[bool]
    ExcludeUppercase: Optional[bool]
    GenerateStringKey: Optional[str]
    IncludeSpace: Optional[bool]
    PasswordLength: Optional[int]
    RequireEachIncludedType: Optional[bool]
    SecretStringTemplate: Optional[str]


class ReplicaRegion(TypedDict):
    Region: Optional[str]
    KmsKeyId: Optional[str]


class Tag(TypedDict):
    Key: Optional[str]
    Value: Optional[str]


REPEATED_INVOCATION = "repeated_invocation"


class SecretsManagerSecretProvider(ResourceProvider[SecretsManagerSecretProperties]):
    TYPE = "AWS::SecretsManager::Secret"  # Autogenerated. Don't change
    SCHEMA = util.get_schema_path(Path(__file__))  # Autogenerated. Don't change

    def create(
        self,
        request: ResourceRequest[SecretsManagerSecretProperties],
    ) -> ProgressEvent[SecretsManagerSecretProperties]:
        """
        Create a new resource.

        Primary identifier fields:
          - /properties/Id



        Create-only properties:
          - /properties/Name

        Read-only properties:
          - /properties/Id



        """
        model = request.desired_state

        # TODO: validations

        if not request.custom_context.get(REPEATED_INVOCATION):
            # this is the first time this callback is invoked
            # TODO: defaults
            # TODO: idempotency
            # TODO: actually create the resource
            request.custom_context[REPEATED_INVOCATION] = True
            return ProgressEvent(
                status=OperationStatus.IN_PROGRESS,
                resource_model=model,
                custom_context=request.custom_context,
            )

        # TODO: check the status of the resource
        # - if finished, update the model with all fields and return success event:
        #   return ProgressEvent(status=OperationStatus.SUCCESS, resource_model=model)
        # - else
        #   return ProgressEvent(status=OperationStatus.IN_PROGRESS, resource_model=model)

        raise NotImplementedError

    def read(
        self,
        request: ResourceRequest[SecretsManagerSecretProperties],
    ) -> ProgressEvent[SecretsManagerSecretProperties]:
        """
        Fetch resource information


        """
        raise NotImplementedError

    def delete(
        self,
        request: ResourceRequest[SecretsManagerSecretProperties],
    ) -> ProgressEvent[SecretsManagerSecretProperties]:
        """
        Delete a resource


        """
        raise NotImplementedError

    def update(
        self,
        request: ResourceRequest[SecretsManagerSecretProperties],
    ) -> ProgressEvent[SecretsManagerSecretProperties]:
        """
        Update a resource


        """
        raise NotImplementedError
