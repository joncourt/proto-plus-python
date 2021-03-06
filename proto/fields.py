# Copyright 2018 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from enum import EnumMeta

from google.protobuf import descriptor_pb2

from proto.primitives import ProtoType


class Field:
    """A representation of a type of field in protocol buffers."""

    def __init__(
        self,
        proto_type,
        *,
        number: int,
        message=None,
        enum=None,
        oneof: str = None,
        json_name: str = None,
        optional: bool = False
    ):
        # This class is not intended to stand entirely alone;
        # data is augmented by the metaclass for Message.
        self.mcls_data = {}
        self.parent = None

        # If the proto type sent is an object or a string, it is really
        # a message or enum.
        if not isinstance(proto_type, int):
            # Note: We only support the "shortcut syntax" for enums
            # when receiving the actual class.
            if isinstance(proto_type, EnumMeta):
                enum = proto_type
                proto_type = ProtoType.ENUM
            else:
                message = proto_type
                proto_type = ProtoType.MESSAGE

        # Save the direct arguments.
        self.number = number
        self.proto_type = proto_type
        self.message = message
        self.enum = enum
        self.json_name = json_name
        self.optional = optional
        self.oneof = oneof

        # Fields are neither repeated nor maps.
        # The RepeatedField and MapField subclasses override these values
        # in their initializers.
        self.repeated = False

        # Once the descriptor is accessed the first time, cache it.
        # This is important because in rare cases the message or enum
        # types are written later.
        self._descriptor = None

    @property
    def descriptor(self):
        """Return the descriptor for the field."""
        proto_type = self.proto_type
        if not self._descriptor:
            # Resolve the message type, if any, to a string.
            type_name = None
            if isinstance(self.message, str):
                if not self.message.startswith(self.package):
                    self.message = "{package}.{name}".format(
                        package=self.package, name=self.message,
                    )
                type_name = self.message
            elif self.message:
                if hasattr(self.message, "DESCRIPTOR"):
                    type_name = self.message.DESCRIPTOR.full_name
                else:
                    type_name = self.message.meta.full_name
            elif self.enum:
                # Nos decipiat.
                #
                # As far as the wire format is concerned, enums are int32s.
                # Protocol buffers itself also only sends ints; the enum
                # objects are simply helper classes for translating names
                # and values and it is the user's job to resolve to an int.
                #
                # Therefore, the non-trivial effort of adding the actual
                # enum descriptors seems to add little or no actual value.
                #
                # FIXME: Eventually, come back and put in the actual enum
                # descriptors.
                proto_type = ProtoType.INT32

            # Set the descriptor.
            self._descriptor = descriptor_pb2.FieldDescriptorProto(
                name=self.name,
                number=self.number,
                label=3 if self.repeated else 1,
                type=proto_type,
                type_name=type_name,
                json_name=self.json_name,
                proto3_optional=self.optional,
            )

        # Return the descriptor.
        return self._descriptor

    @property
    def name(self) -> str:
        """Return the name of the field."""
        return self.mcls_data["name"]

    @property
    def package(self) -> str:
        """Return the package of the field."""
        return self.mcls_data["package"]

    @property
    def pb_type(self):
        """Return the composite type of the field, or None for primitives."""
        # For enums, return the Python enum.
        if self.enum:
            return self.enum

        # For non-enum primitives, return None.
        if not self.message:
            return None

        # Return the internal protobuf message.
        if hasattr(self.message, "_meta"):
            return self.message.pb()
        return self.message


class RepeatedField(Field):
    """A representation of a repeated field in protocol buffers."""

    def __init__(self, proto_type, *, number: int, message=None, enum=None):
        super().__init__(proto_type, number=number, message=message, enum=enum)
        self.repeated = True


class MapField(Field):
    """A representation of a map field in protocol buffers."""

    def __init__(self, key_type, value_type, *, number: int, message=None, enum=None):
        super().__init__(value_type, number=number, message=message, enum=enum)
        self.map_key_type = key_type


__all__ = (
    "Field",
    "MapField",
    "RepeatedField",
)
